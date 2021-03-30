"""
Translate a XML CSDMG metadata file to the
YAML format used by the data collector.
author: Christian Ariza
"""
import json
import re
import xml.etree.ElementTree as ET
from itertools import chain
from pathlib import Path, PurePath

import jsonschema
import yaml
from jsonschema import Draft7Validator, validators
from shapely import wkt
from shapely.geometry import Polygon

try:
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Dumper

mappings_single = {
    "global_attributes.summary": "idinfo/descript/abstract",
    "global_attributes.title": "idinfo/citation/citeinfo/title",
    "global_attributes.project": "idinfo/citation/citeinfo/title",
    "global_attributes.institution": "idinfo/citation/citeinfo/origin",
    "global_attributes.start_date": "idinfo/timeperd/timeinfo/rngdates/begdate",
    "global_attributes.end_date": "idinfo/timeperd/timeinfo/rngdates/enddate",
    "global_attributes.cdm_data_type": "spdoinfo/direct",
    "global_attributes.source": "idinfo/citation/citeinfo/pubinfo/publish",
    "global_attributes.references": "idinfo/citation/citeinfo/onlink",
    "global_attributes.creation_date": "idinfo/citation/citeinfo/pubdate",
    "global_attributes.published_date": "idinfo/citation/citeinfo/pubdate",
}


def extend_with_default(validator_class):
    """
    Extend the validator to set the defaults. This validator will, though,
    fail with required fields that have a default, so it need to be used
    twice in that case (one to fill defaults, and the second to validate.)
    """
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        required_ = schema["required"]
        for property_, subschema in properties.items():
            if "default" in subschema and property_ in required_:
                instance.setdefault(property_, subschema["default"])

        for error in validate_properties(validator, properties, instance, schema):
            yield error

    return validators.extend(
        validator_class,
        {"required": lambda w, x, y, z: None, "properties": set_defaults},
    )


DefaultValidatingDraft7Validator = extend_with_default(Draft7Validator)


def get_bbox_wkt(xml_parse):

    """
    Create a WKT expression from the Bounding box defined
    in the xml:
        <spdom>
      <bounding>
        <westbc>-95.018</westbc>
        <eastbc>-94.353</eastbc>
        <northbc>29.890</northbc>
        <southbc>29.496</southbc>
      </bounding>
       </spdom>
    """
    bounds = xml_parse.find("idinfo/spdom/bounding")
    x_1 = float(bounds.find("westbc").text)
    x_2 = float(bounds.find("eastbc").text)
    y_1 = float(bounds.find("northbc").text)
    y_2 = float(bounds.find("southbc").text)
    return wkt.dumps(Polygon([(x_1, y_1), (x_1, y_2), (x_2, y_2), (x_2, y_1)]))


def get_keywords(xml_parse):
    """
    Generate a list of keywords
    """
    keywords_theme = xml_parse.findall("idinfo/keywords/theme/themekey")
    keywords_place = xml_parse.findall("idinfo/keywords/place/placekey")
    keywords = chain(keywords_theme, keywords_place)
    return ",".join((k.text for k in keywords))


def get_metadata_contact(xml_parse):
    """Generate a metadata object from the
    metainfo object on the XML
    """
    metadata_contact = {}
    metadata_contact["email"] = xml_parse.find("//metainfo//cntemail").text
    metadata_contact["name"] = xml_parse.find("//metainfo//cntemail").text or None
    metadata_contact["role"] = "publisher"
    return metadata_contact


def get_lineage(xml_parse):
    """
    Create a lineage object based on the lineage element
    of the source XML
    """
    src_info = xml_parse.findall("//lineage/srcinfo")
    steps = xml_parse.findall("//lineage/procstep")
    lineage = {}
    if len(src_info) > 0:
        lineage["source"] = "Multiple"
        sources_list = []
        for src in src_info:
            source_obj = {}
            source_obj["title"] = src.find(".//title").text.strip() or None
            source_obj["author"] = src.find(".//origin").text.strip() or None
            source_obj["pub_date"] = src.find(".//pubdate").text.strip() or None
            source_obj["srccitea"] = src.find(".//srccitea").text.strip() or None
            sources_list.append(source_obj)
        lineage["source_list"] = sources_list
    regex = r"\s+"
    for step in steps:
        process = f"""  - {step.find('.//procdate').text.strip() or 'No Date Set'},
    sources {step.find('.//srcused').text.strip() or 'N/A'}:
    { re.sub(regex, ' ', step.find('.//procdesc').text.strip())}
"""
        lineage["process"] = lineage.get("process", "") + process
    lineage["process"] = lineage.get("process", "").rstrip()
    lineage["description"] = "See the sources and process information"
    return lineage


def dot2object(dotted_dict):
    """
    Create a object based on a dict that use
    dot notation keys.
    """
    obj = {}
    for k in dotted_dict:
        keys = k.split(".")
        new_key = keys[0]
        if not new_key in obj:
            obj[new_key] = {}
        obj[new_key][".".join(keys[1:])] = dotted_dict.get(k)
    for key in obj:
        if "." in key:
            _obj = dot2object(obj[key])
            obj[key] = _obj
    return obj


def convert_csdmg_xml_to_twi_yaml(
    source_file, target=None, schema="metadata.jsonschema.json"
):
    """Convert a CSDMG XML metadata file to a Yaml file with the desired format."""
    if not target:
        parent = (
            Path(
                source_file
                if isinstance(source_file, (str, PurePath))
                else source_file.name
            )
            .absolute()
            .parent
        )
        target = Path.joinpath(parent, "metadata.yaml")
    xml_parse = ET.parse(source_file)
    tmp_output = {}
    for _k in mappings_single:
        results = xml_parse.findall(mappings_single[_k])
        for _r in results:
            tmp_output[_k] = re.sub(r"\s+", " ", _r.text.strip())
    output = dot2object(tmp_output)
    output["index_location"] = "./"
    output["bounds_wkt"] = get_bbox_wkt(xml_parse)
    output["global_attributes"]["keywords"] = get_keywords(xml_parse)
    output["metadata_contacts"] = get_metadata_contact(xml_parse)
    output["lineage"] = get_lineage(xml_parse)
    with open(schema, "rb") as schema_file:
        _schema = json.load(schema_file)
        fill_with_defaults = DefaultValidatingDraft7Validator(_schema)
        fill_with_defaults.is_valid(output)  # fill with defaults
        validator = jsonschema.Draft7Validator(_schema)
        if not validator.is_valid(output):
            print(list(validator.iter_errors(output)))
    with open(target, "w") as target_file:
        yaml.dump(output, Dumper=Dumper, stream=target_file)
