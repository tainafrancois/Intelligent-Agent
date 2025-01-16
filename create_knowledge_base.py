import pandas as pd
import rdflib
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import FOAF, RDFS, RDF, XSD
from os import listdir
import os.path
import csv
# import parser object from tika
from tika import parser
import spacy
import spacy_dbpedia_spotlight
from spacy.matcher import Matcher
import re

CU_SR_OPEN_DATA_CATALOG = 'csv/CU_SR_OPEN_DATA_CATALOG.csv'
CATALOG = 'csv/CATALOG.csv'
STUDENTS = 'csv/Students_Grades.csv'
OUTPUT = 'knowledgeGraph.ttl'
DBpedia_Endpoint = 'http://localhost:2222/rest'
# Namespace
rbps = Namespace('http://roboprof.com/schema#')
rbpd = Namespace('http://roboprof.com/data#')
dbp = Namespace("http://dbpedia.org/resource/")
wiki = Namespace("http://www.wikidata.org/entity/")
# Parse vocabularies.ttl
graph = rdflib.Graph()
graph.bind("rbps", rbps)
graph.bind("rbpd", rbpd)
graph.bind("dbp", dbp)
graph.bind("wiki", wiki)

# Spacy initialization
nlp = spacy.load('en_core_web_md')
#nlp.add_pipe('dbpedia_spotlight', config={'dbpedia_rest_endpoint': DBpedia_Endpoint, 'process': 'candidates', 'confidence': 0.75})
nlp.add_pipe("entityfishing")
#nlp.add_pipe('dbpedia_spotlight', config={'dbpedia_rest_endpoint': DBpedia_Endpoint, 'process': 'candidates', 'confidence': 0.75})
#nlp.add_pipe('dbpedia_spotlight', config={'dbpedia_rest_endpoint': DBpedia_Endpoint, 'process': 'annotate', 'confidence': 0.80}, first=True)

def strip(word):
    if word:
        return word.strip()    
    return word

def getLocalURI(courseName, fileName, folder = None):
    path = 'file:///home/roboprof/'
    if folder == None:
        return path + '/'.join([courseName, fileName]).replace('\\','/')
    return path + '/'.join([courseName, folder, fileName])
    
def load_course_info():
    
    '''
    In CU_SR_OPEN_DATA_CATALOG.csv
    Col 1: Course Subject
    Col 2: Course Number
    Col 3: Course Name
    Col 4: Course Credits
    '''
    cu_catalogDf = pd.read_csv(CU_SR_OPEN_DATA_CATALOG, 
                               names=['subject', 'number', 'name', 'credits'], 
                               usecols=[1,2,3,4], 
                               header=0, 
                               encoding = 'utf-16',
                               converters= {
                                'subject' : strip,
                                'number' : strip,
                                'name' : strip,
                                'credits': strip})
    cu_catalogDict = cu_catalogDf.to_dict(orient='records')
    '''
    In CATALOG.csv
    Col 6: Course Subject
    Col 7: Course Number
    Col 9: Description
    Col 12: Course Link
    '''
    catalogDf = pd.read_csv(CATALOG, 
                            names=['subject', 'number', 'description', 'link'], 
                            usecols=[6,7,9,12], 
                            header=0, 
                            converters= {
                            'subject' : strip,
                            'number' : strip,
                            'description' : strip,
                            'link': strip}
    )
    courses = []
    for course in cu_catalogDict:
        rows = catalogDf.loc[(catalogDf['subject'] == course['subject']) & (catalogDf['number'] == course['number'])]
        if len(rows) > 0:
            course['description'] = rows.iloc[0]['description']
            course['link'] = rows.iloc[0]['link']
            courses.append(course)
    return courses
'''
{40057324: {first_name: Sutton, last_name: Randall, email: sutton@example.com, courses: {comp445: [C,D]}, {comp474: [A]} }}
'''

def load_students():
    students = {}
    with open(STUDENTS, newline='') as csvfile:
        reader = csv.DictReader(csvfile, quotechar='|')
        for row in reader:
            id = row['student_id']
            course = row['course_subject'] + row['course_number']
            if id not in students:
                students[id] = {}
                students[id]['first_name'] = row['first_name']
                students[id]['last_name'] = row['last_name']
                students[id]['email'] = row['email']
                students[id]['courses'] = {}
            if course not in students[id]['courses']:
                students[id]['courses'][course] = []
            students[id]['courses'][course].append({'grade': row['grade'], 'date': row['date']})
    return students

def add_topics_to_graph(ent):
    if (ent.text.isspace()):
        return None
    filterList = set('abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    newEnt = ''.join(filter(filterList.__contains__, ent.text))
    if (newEnt == ''):
        return None
    
    topicKey = re.sub(' +', '_',newEnt.strip())

    topicNode = rbpd[topicKey]
    # Add topic to the graph
    graph.add((topicNode, RDF.type, rbps.Topic))
    graph.add((topicNode, RDFS.label, Literal(newEnt.strip(), lang="en")))
    if (ent._.url_wikidata != None):
        graph.add((topicNode, RDFS.seeAlso, rdflib.term.URIRef(wiki[ent._.kb_qid])))
    #if (ent.kb_id_ != None and ent.kb_id_ != ""):
        #graph.add((topicNode, RDFS.seeAlso, rdflib.term.URIRef(ent.kb_id_)))
    return {"key": topicKey, "name": newEnt}

def words_in_string(word_list, a_string):
    return set(word_list).intersection(a_string.split())

def linkToWikidata(text):
    matcher = Matcher(nlp.vocab)

    propn_patterns = [
        [{'POS':'PROPN'}],
    ]
    matcher.add("PROPN", propn_patterns)
    n_patterns = [
        [{'POS':'NOUN'}],
    ]
    matcher.add("NOUN", n_patterns)
    entityKeys = []
    if (len(text) > nlp.max_length):
        nlp.max_length = len(text)


    doc = nlp(text)

    matches = matcher(doc)
    namedEntities = []
    for _, start, end in matches:
        span = doc[start:end]
        namedEntities.append(span.text)
    for ent in doc.ents:
        if words_in_string(namedEntities,ent.text) and ent._.nerd_score != None and float(ent._.nerd_score) >= 0.60:
            entityDict = add_topics_to_graph(ent)
            if (entityDict != None):
                entityKeys.append(entityDict)

    return entityKeys


def parseFileToText(fileName, path):
    print("Loading...............................", fileName)
    # Convert Course outline to text
    try:
        parsed_pdf = parser.from_file(os.path.join(path,fileName).replace('\\','/')) 

    except:
        return
    # saving content of pdf 
    data = parsed_pdf['content']
    txtFile = '.'.join([fileName.split('.')[0],"txt"])
    with open(os.path.join(path,txtFile), "w", encoding='utf-8') as file:
           file.write(data)
    return linkToWikidata(data)
            

def add_student_to_graph(students, univeristy):
    for IDNumber, studentInfo in students.items() :
        # create a Node for the student
        student_node = rbpd[IDNumber]
        first_name = studentInfo['first_name']
        last_name = studentInfo['last_name']
        email = studentInfo['email']
        courses = studentInfo['courses']
        # Add a student to graph
        graph.add((student_node, RDF.type, rbps.Student))
        # Add a student's ID number
        graph.add((student_node, rbps.IDNumber, Literal(IDNumber, datatype=XSD.integer)))
        # Add a student's first name
        graph.add((student_node, FOAF.givenName, Literal(first_name, lang='en'))) 
        # Add a student's last name
        graph.add((student_node, FOAF.familyName, Literal(last_name,lang='en'))) 
        # Add a student's email
        graph.add((student_node, FOAF.mbox, rdflib.URIRef(':'.join(['mailto',email])))) 
        # Add a student's univeristy
        graph.add((student_node, rbps.hasEnrolled, univeristy))

        #Add student's attempts
        for courseID, grades in courses.items():
            attemp_node = rbpd['_'.join([courseID,IDNumber])]
            graph.add((attemp_node, RDF.type, rbps.Attempt))
            graph.add((attemp_node, rbps.AttemptCourse, rbpd[courseID]))
            for grade in grades:
                gradeNode = rbpd['_'.join([courseID,IDNumber,grade['date'].replace('-','_')])]
                graph.add((gradeNode, rbps.Value, Literal(grade['grade'], datatype=XSD.decimal)))
                graph.add((gradeNode, rbps.Date, Literal(grade['date'], datatype=XSD.date)))
                graph.add((attemp_node, rbps.AttemptGrade, gradeNode))
                if float(grade['grade']) >= 50.0:
                    #print(list(graph.objects(rbpd[courseID], rbps.CoveredTopic)))
                    for topicNode in graph.objects(rbpd[courseID], rbps.CoveredTopic):
                        graph.add((student_node, rbps.Competency, topicNode))
            graph.add((student_node, rbps.hasAttempt, attemp_node))
                            

def add_course_to_graph(courses, university):
    for course in courses:
        courseKey = course['subject'] + course['number']
        courseNode = rbpd[courseKey]
        # Add a course to graph
        graph.add((courseNode, RDF.type, rbps.Course))
        # Add a course name
        graph.add((courseNode, RDFS.label, Literal(course['name'], lang="en")))
        # Add a course subject
        graph.add((courseNode, rbps.CourseSubject, Literal(course['subject'], lang="en")))
        # Add a course number
        graph.add((courseNode, rbps.CourseNumber, Literal(course['number'], lang="en")))
        # Add a course description
        graph.add((courseNode, rbps.CourseDescription, Literal(course['description'], lang="en")))
        # Add a course credits
        graph.add((courseNode, rbps.CourseCredits, Literal(course['credits'], datatype=XSD.decimal)))
        # Add a course link
        if course['link'] and (' ' not in course['link']):
            graph.add((courseNode, RDFS.seeAlso, rdflib.term.URIRef(course['link'])))
        # Assign a course to a university
        graph.add((courseNode, rbps.CourseOfUniversity, university))


def add_materials_to_course(courseName):
    course = rbpd[courseName]
    coursePath = os.path.join('courses/', courseName).replace('/','\\')

    # Add course outline
    courseOutlineURI = rdflib.term.URIRef(getLocalURI(courseName, 'CourseOutline.pdf'))
    print("\t----Loading Course Outline...")
    graph.add((course, rbps.CourseOutline, courseOutlineURI))
    topicsKey = parseFileToText('CourseOutline.pdf',coursePath)
    
    for topicKey in topicsKey:
        # Add a topic to a course
        graph.add((course, rbps.CoveredTopic, rbpd[topicKey["key"]]))
        # Add a provenance b/w topics and course outline
        graph.add((rbpd[topicKey["key"]], rbps.TopicProvenance, courseOutlineURI))
    lecturePaths = os.path.join(coursePath, 'lectures')
    for lectureNumber in listdir(lecturePaths):
        print(f"\t\t----Loading Lecture {lectureNumber}...")
        # Create lecture node
        lectureNode = rbpd['_'.join([courseName,'Lecture',str(lectureNumber)])] #not sure
        # Add Lecture
        graph.add((lectureNode, RDF.type, rbps.Lecture))
        # Add a lecture number
        graph.add((lectureNode, rbps.LectureNumber, Literal(lectureNumber, datatype=XSD.integer)))
        currentPath = os.path.join(lecturePaths, lectureNumber)
        for material in listdir(currentPath):
            print(f"\t\t\t----Loading {material}...")
            filePath = os.path.join(currentPath, material)
            for file in listdir(filePath):
                path = os.path.join(filePath, file)
                if os.path.isdir(path) or file.endswith('.txt'):
                    continue
                node = rdflib.term.URIRef(getLocalURI(filePath, file).replace(" ",""))
                fileName = file.split('.')[0]
                coveredTopic = parseFileToText(file,filePath)
                if (material == 'slides'):  
                    graph.add((node, RDF.type, rbps.Slides))
                    graph.add((node, RDFS.label, Literal(fileName, lang='en')))
                    graph.add((lectureNode, rbps.hasSlides, node))
                elif (material == 'worksheets'):
                    graph.add((node, RDF.type, rbps.Worksheets))
                    graph.add((node, RDFS.label, Literal(fileName, lang='en')))
                    graph.add((lectureNode, rbps.hasWorksheets, node))
                elif (material == 'readings'):
                    graph.add((node, RDF.type, rbps.Readings))
                    graph.add((node, RDFS.label, Literal(fileName, lang='en')))
                    graph.add((lectureNode, rbps.hasReadings, node))
                elif (material == 'labs'):
                    graph.add((node, RDF.type, rbps.Labs))
                    graph.add((node, RDFS.label, Literal(fileName, lang='en')))
                    graph.add((lectureNode, rbps.hasLabs, node))

                topicNames = []
                for topic in coveredTopic:
                    # Add topic provenance
                    graph.add((rbpd[topic["key"]], rbps.TopicProvenance, lectureNode))
                    graph.add((rbpd[topic["key"]], rbps.TopicProvenance, node))
                    graph.add((course, rbps.CoveredTopic, rbpd[topic["key"]]))
                    # Add topic to each lecture content
                    graph.add((node,rbps.aboutTopic,rbpd[topic["key"]]))
                    # Add a lecture topic
                    graph.add((lectureNode, rbps.TopicLecture, rbpd[topic["key"]]))
                    topicNames.append(topic["name"])
                graph.add((lectureNode, RDFS.label, Literal(str(lectureNumber), lang='en')))
        # Assign lectures to a course
        graph.add((lectureNode, rbps.LectureOfCourse, course))

def populate_knowledge():
    
    concordiaUniversity = rbpd['Concordia_University']
    graph.add((concordiaUniversity, RDF.type, rbps.University))
    graph.add((concordiaUniversity, FOAF.name, Literal('Concordia University', lang="en")))
    graph.add((concordiaUniversity, RDFS.label, Literal('Concordia University', lang="en")))
    graph.add((concordiaUniversity, RDFS.seeAlso, dbp['Concordia_University']))
    print("Loading courses....")
    courses = load_course_info()
    add_course_to_graph(courses, concordiaUniversity)
    print("Loading material to course COMP 474....")
    add_materials_to_course('COMP474')
    print("Loading material to course COMP 445....")
    add_materials_to_course('COMP445')

    ## Add students to graph here
    print("Loading students....")
    students = load_students()
    add_student_to_graph(students, concordiaUniversity)

    # Write the merged graph to a file in Turtle format
    
    with open("Knowledge_Base.ttl", "w", encoding='utf-8') as f:
        f.write(graph.serialize(format='turtle'))
    # Write the merged graph to a file in N-Triples format
    with open("Knowledge_Base.nt", "w", encoding='utf-8') as f:
        f.write(graph.serialize(format='nt'))

if __name__ == "__main__":
    populate_knowledge()
    


