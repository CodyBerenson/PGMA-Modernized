import sys
import subprocess
import re
import os
from pbjson import pb2json
from AST_pb2 import Element as EL
from google.protobuf.internal import encoder
import pdb
import xml.etree.ElementTree as ET
import cgi
import _ast
from Element import *
from Unit import *
from Literal import *
#from _ast.Element import *
#from _ast._EL.Unit import *
#from _ast._EL.Literal import *
import flatbuffers

debug = False
mapping = {}

def dumpTree(root, rootAST):
    tag = re.sub(r"{.*}", "", root.tag)
    if root.text:
       rootAST.text = root.text
    if root.tail:
       rootAST.tail = root.tail
    if tag == "unit":
        rootAST.unit.filename = root.attrib['filename']
        rootAST.unit.revision = root.attrib['revision']
        lang = root.attrib['language'] 
        if lang == "C++":
            lang = "CXX"
        rootAST.unit.language = EL.Unit.LanguageType.DESCRIPTOR.values_by_name[lang].__dict__['number']
        if root.attrib.get('item') != None:
            rootAST.unit.item = root.attrib['item']
        tag = tag + "_KIND"
    elif tag == "literal":
        if root.attrib and root.attrib['type']:
            rootAST.literal.type = EL.Literal.LiteralType.DESCRIPTOR.values_by_name[root.attrib['type'] + "_type"].__dict__['number']
    rootAST.kind = EL.Kind.DESCRIPTOR.values_by_name[tag.upper()].__dict__['number']
    for child in root.findall("*"):
        childAST = rootAST.child.add()
        dumpTree(child, childAST)

def dumpXML(out, rootAST):
    tag = EL.Kind.DESCRIPTOR.values[rootAST.kind].name.lower()
    if tag == "unit_kind":
        tag = tag[:len(tag)-5] # strip the "_kind" suffix
        lang = EL.Unit.LanguageType.DESCRIPTOR.values[rootAST.unit.language].name
        if lang == "CXX":
            lang = "C++"
            lan = "cpp"
        else:
            lan = lang.lower()
        if rootAST.unit.item:
            item = " item=\"" + item + "\""
        else: 
            item = ""
        start_tag = "unit"  \
            + " xmlns=\"http://www.srcML.org/srcML/src\"" \
            + " xmlns:" + lan + "=\"http://www.srcML.org/srcML/" + lan + "\"" \
            + " revision=\"" + rootAST.unit.revision + "\"" \
            + " language=\"" + lang + "\"" \
            + " filename=\"" + rootAST.unit.filename + "\"" \
            + item
    elif tag == "literal":
        if rootAST.literal.type != None:
            n = EL.Literal.LiteralType.DESCRIPTOR.values[rootAST.literal.type].name 
            type = " type=\"" + n[0:len(n)-5] + "\""  # strip the "_type" suffix
        else:
            type = ""
        start_tag = "literal" \
            + type
    else:
        start_tag = tag
    if tag != "unit" or rootAST.unit.filename != "":
        out.write("<" + start_tag + ">")
    if rootAST.text:
       out.write(cgi.escape(rootAST.text).encode('ascii', 'xmlcharrefreplace'))
    for childAST in rootAST.child:
        dumpXML(out, childAST)
    if tag != "unit" or rootAST.unit.filename != "":
       out.write("</" + tag + ">")
    if rootAST.tail:
       out.write(cgi.escape(rootAST.tail).encode('ascii', 'xmlcharrefreplace'))

def dumpFlatBuffers(root, builder):
    tag = re.sub(r"{.*}", "", root.tag)
    rootText = None
    rootTail = None
    rootFilename = None
    rootLang = None
    rootItem = None
    if root.text:
        rootText = builder.CreateString(root.text)
    if root.tail:
        rootTail = builder.CreateString(root.tail)
    if tag == "unit" and root.attrib and root.attrib['filename']:
        rootFilename = builder.CreateString(root.attrib['filename'])
    if tag == "unit" and root.attrib and root.attrib['revision']:
        rootRevision = builder.CreateString(root.attrib['revision'])
    if tag == "unit" and root.attrib:
        lang = root.attrib['language'] 
        if lang: 
            if lang == "C++":
                lang = "CXX"
        rootLang = EL.Unit.LanguageType.DESCRIPTOR.values_by_name[lang].__dict__['number']
    if tag == "unit" and root.attrib and root.attrib.get('item') != None:
        rootItem = root.attrib['item']
    childASTs=[]
    for child in root.findall("*"):
        childASTs.append(dumpFlatBuffers(child, builder))
    if tag == "unit":
        UnitStart(builder)
        UnitAddFilename(builder, rootFilename) 
        UnitAddRevision(builder, rootRevision) 
        UnitAddLanguage(builder, rootLang) 
        if rootItem != None: 
            UnitAddItem(builder, rootItem) 
        unit = UnitEnd(builder)
        tag = tag + "_KIND"
    elif tag == "literal":
        if root.attrib and root.attrib['type']:
            LiteralStart(builder)
            LiteralAddType(builder, EL.Literal.LiteralType.DESCRIPTOR.values_by_name[root.attrib['type'] + "_type"].__dict__['number'])
            literal = LiteralEnd(builder)
    ElementStart(builder)
    if rootText:
        ElementAddText(builder, rootText)
    if rootTail:
        ElementAddTail(builder, rootTail)
    ElementAddKind(builder, EL.Kind.DESCRIPTOR.values_by_name[tag.upper()].__dict__['number'])
    for childAST in childASTs:
        ElementAddChild(builder, childAST)
    return ElementEnd(builder)

def read_xml(input_filename, output_filename):
    if debug:
        pdb.set_trace()
    output_basename, output_extension = os.path.splitext(output_filename)
    out_file = open(output_filename, "a")
    tree = ET.parse(input_filename)
    root = tree.getroot()
    if output_extension == ".pb": 
        unit = EL()
        dumpTree(root, unit)
        serializedMessage = unit.SerializeToString()
        out_file.write(serializedMessage)
        out_file.close()
    elif output_extension == ".fbs":
        builder = flatbuffers.Builder(0)
        rootFBS = dumpFlatBuffers(root, builder)
        ElementStart(builder)
        ElementAddChild(builder, rootFBS)
        data = ElementEnd(builder)
        builder.Finish(data)
        gen_buf, gen_off = builder.Bytes, builder.Head()
        out_file.write(gen_buf[gen_off:])
        out_file.close()

def read_pb(input_filename, output_filename):
    data = EL()
    with open(input_filename, 'rb') as f:
       data.ParseFromString(f.read())
       f.close()
       output_basename, output_extension = os.path.splitext(output_filename)
       with open(output_filename, 'w') as out:
           if output_extension == ".json":
               out.write(pb2json(data))
               out.close()
           elif output_extension == ".xml":
               out.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n");
               dumpXML(out, data)
               out.write("\n")
               out.close()
           elif output_extension == ".cpp" or output_extension == ".cc" or output_extension == ".java":
               with open(output_filename + ".xml", 'w') as xml_out:
                   dumpXML(xml_out, data)
                   xml_out.close()
               p = subprocess.Popen(["srcml", output_filename + ".xml"], stdout=subprocess.PIPE)
               for line in p.stdout:
                   out.write(line)
               out.close()
               os.remove(output_filename + ".xml")
           else: # do not output, to test performance of loading protobuf
               out.close()

def read_fbs(input_filename, output_filename):
    with open(input_filename, 'rb') as f:
       buf = f.read()
       buf = bytearray(buf)
       data = Element.GetRootAsElement(buf, 0)
       output_basename, output_extension = os.path.splitext(output_filename)
       with open(output_filename, 'w') as out:
           if output_extension == ".json":
               out.close()
           elif output_extension == ".xml":
               out.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n");
               out.write("\n")
               out.close()
           elif output_extension == ".cpp" or output_extension == ".cc" or output_extension == ".java":
               out.close()
           else: # do not output, to test performance of loading protobuf
               out.close()

#if __name__ == "__main__":
def main():
       if sys.argv[1] == "-g": 
           debug = True
           sys.argv = sys.argv[1:] # shift
       if (os.path.exists(sys.argv[2])):
           os.remove(sys.argv[2])
       input_filename, input_extension = os.path.splitext(sys.argv[1])
       if (input_extension == ".xml"):
           read_xml(sys.argv[1], sys.argv[2])
       if (input_extension == ".pb"):
           read_pb(sys.argv[1], sys.argv[2])
       if (input_extension == ".fbs"):
           read_fbs(sys.argv[1], sys.argv[2])
