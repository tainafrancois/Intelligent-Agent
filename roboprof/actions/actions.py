from typing import Any, Text, Dict, List
from SPARQLWrapper import SPARQLWrapper, CSV, JSON
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import csv


def runQuery(query, format=CSV):
    sparql = SPARQLWrapper("http://localhost:3030/Roboprof/query")
    sparql.setReturnFormat(format)
    sparql.setQuery(query)
    try:
        ret = sparql.queryAndConvert()
        return ret
    except Exception as e:
        print(e)


def processCSVdata(csvText):
    csv_rows = csv.reader(csvText.splitlines())
    # Skip the header row
    return list(csv_rows)[1:]


class ActionUniversityInfo(Action):
    def name(self):
        return "action_university_info"

    def run(self, dispatcher, tracker, domain):
        # Get the user's input
        university = tracker.get_slot('university')
        query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rbps: <http://roboprof.com/schema#>

        SELECT ?courseSubject ?courseNumber ?courseLabel
        WHERE {
	        ?course rdfs:label ?courseLabel.
	        ?course rbps:CourseSubject ?courseSubject.
	        ?course rbps:CourseNumber ?courseNumber.
	        ?course rbps:CourseOfUniversity ?university.
            ?university rdfs:label '""" + university + """'@en.
        }
        """
        # Submit query
        res = runQuery(query)
        rows = processCSVdata(res.decode('utf-8'))
        if len(rows) == 0:
            dispatcher.utter_message(text=f"Sorry, I could not find any courses that are offered by {university}.")
        else:
            dispatcher.utter_message(text=f"Here are courses that are offered by {university}:\n")
            for row in rows:
                dispatcher.utter_message(text=f"{row[0]}{row[1]}: {row[2]}\n")

        return []


# Q8
class ActionLectureContent(Action):
    def name(self):
        return "action_lecture_content"

    def run(self, dispatcher, tracker, domain):
        lecture_number = tracker.get_slot('lecture_number')
        course_subject = tracker.get_slot('course_subject')
        course_number = tracker.get_slot('course_number')
        content_type = tracker.get_slot('content_type')

        content_property_map = {
            "readings": "rbps:hasReadings",
            "labs": "rbps:hasLabs",
            "slides": "rbps:hasSlides",
            "worksheets": "rbps:hasWorksheets"
        }

        content_property = content_property_map.get(content_type)

        if not content_property:
            dispatcher.utter_message(text=f"Sorry, I don't recognize the content type '{content_type}'.")
            return []

        query = f"""
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rbps: <http://roboprof.com/schema#>
        PREFIX rbpd: <http://roboprof.com/data#>

        SELECT ?material ?material_label ?material_type_label
        WHERE {{
            ?material rdf:type ?material_type ;
                     rdfs:label ?material_label.

            ?material_type rdfs:subClassOf rbps:LectureContent ;
                           rdfs:label ?material_type_label.

            ?lecture {content_property} ?material ;
                     rbps:LectureNumber '{lecture_number}'^^xsd:integer ;
                     rbps:LectureOfCourse ?course.

            ?course rdf:type rbps:Course ;
                    rbps:CourseSubject '{course_subject}'@en ;
                    rbps:CourseNumber '{course_number}'@en.
        }}
        """
        res = runQuery(query)
        rows = processCSVdata(res.decode('utf-8'))
        if len(rows) == 0:
            dispatcher.utter_message(
                text=f"No {content_type} found for lecture number {lecture_number} in {course_subject} {course_number}.")
        else:
            dispatcher.utter_message(
                text=f"{content_type.capitalize()} for lecture number {lecture_number} in {course_subject} {course_number}:\n")
            for row in rows:
                dispatcher.utter_message(text=f"Material: {row[1]}, Type: {row[2]}\n")
        return []


# Q9
class ActionTopicReadings(Action):
    def name(self):
        return "action_topic_readings"

    def run(self, dispatcher, tracker, domain):
        topic_label = tracker.get_slot('topic_label')
        course_label = tracker.get_slot('course_label')
        content_type = tracker.get_slot('content_type')

        # Mapping content type to the corresponding property
        content_property_map = {
            "readings": "rbps:hasReadings",
            "labs": "rbps:hasLabs",
            "slides": "rbps:hasSlides",
            "worksheets": "rbps:hasWorksheets"
        }

        content_property = content_property_map.get(content_type)

        if not content_property:
            dispatcher.utter_message(text=f"Sorry, I do not recognize the content type '{content_type}'.")
            return []

        query = f"""
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rbps: <http://roboprof.com/schema#>
        PREFIX rbpd: <http://roboprof.com/data#>

        SELECT ?material ?material_label
        WHERE {{
            ?material rdf:type rbps:{content_type.capitalize()} ;
                     rdfs:label ?material_label.

            ?lecture {content_property} ?material ;
                     rbps:TopicLecture ?topic ;
                     rbps:LectureOfCourse ?course.
            ?topic rdf:type rbps:Topic ;
                   rdfs:label '{topic_label}'@en.

            ?course rdf:type rbps:Course ;
                    rdfs:label '{course_label}'@en.
        }}
        """
        res = runQuery(query)
        rows = processCSVdata(res.decode('utf-8'))
        if len(rows) == 0:
            dispatcher.utter_message(
                text=f"No {content_type} found for the topic '{topic_label}' in the course '{course_label}'.")
        else:
            dispatcher.utter_message(
                text=f"{content_type.capitalize()} for the topic '{topic_label}' in the course '{course_label}':\n")
            for row in rows:
                dispatcher.utter_message(text=f"Material: {row[1]}\n")
        return []


# Q10
class ActionCourseCompetencies(Action):
    def name(self):
        return "action_course_competencies"

    def run(self, dispatcher, tracker, domain):
        course_subject = tracker.get_slot('course_subject')
        course_number = tracker.get_slot('course_number')

        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rbps: <http://roboprof.com/schema#>

        SELECT ?competency ?competencyLabel
        WHERE {{
            ?course rdf:type rbps:Course ;
                    rbps:CourseSubject '{course_subject}'@en;
                    rbps:CourseNumber '{course_number}'@en;
                    rbps:CoveredTopic ?competency.

            ?competency rdfs:label ?competencyLabel.
        }}
        """
        res = runQuery(query)
        rows = processCSVdata(res.decode('utf-8'))
        if len(rows) == 0:
            dispatcher.utter_message(text=f"No competencies found for the course '{course_subject} {course_number}'.")
        else:
            dispatcher.utter_message(text=f"Competencies covered in the course '{course_subject} {course_number}':\n")
            for row in rows:
                dispatcher.utter_message(text=f"Competency: {row[1]}\n")
        return []


# Q11
class ActionStudentGrades(Action):
    def name(self):
        return "action_student_grades"

    def run(self, dispatcher, tracker, domain):
        student_id = tracker.get_slot('student_id')
        course_subject = tracker.get_slot('course_subject')
        course_number = tracker.get_slot('course_number')

        query = f"""
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rbps: <http://roboprof.com/schema#>

        SELECT ?grade
        WHERE {{
            ?student rdf:type rbps:Student ;
                     rbps:IDNumber "{student_id}"^^xsd:integer ;
                     rbps:hasAttempt ?attemptedCourse.

            ?attemptedCourse rdf:type rbps:Attempt;
                             rbps:AttemptCourse ?course ;
                             rbps:AttemptGrade ?grade.

            ?course rdf:type rbps:Course ;
                    rbps:CourseSubject "{course_subject}"@en ;
                    rbps:CourseNumber "{course_number}"@en.
        }}
        """
        res = runQuery(query)
        rows = processCSVdata(res.decode('utf-8'))
        if len(rows) == 0:
            dispatcher.utter_message(
                text=f"No grades found for student with ID '{student_id}' in the course '{course_subject} {course_number}'.")
        else:
            grades = [row[0] for row in rows]
            dispatcher.utter_message(
                text=f"Grades for student with ID '{student_id}' in the course '{course_subject} {course_number}': {', '.join(grades)}")
        return []


# Q12
class ActionPassingStudents(Action):
    def name(self):
        return "action_passing_students"

    def run(self, dispatcher, tracker, domain):
        course_subject = tracker.get_slot('course_subject')
        course_number = tracker.get_slot('course_number')

        query = f"""
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rbps: <http://roboprof.com/schema#>

        SELECT ?student ?id ?firstName ?lastName
        WHERE {{
            ?course rdf:type rbps:Course ;
                    rbps:CourseSubject "{course_subject}"@en ;
                    rbps:CourseNumber "{course_number}"@en .

            ?student rdf:type rbps:Student ;
                     rbps:IDNumber ?id;
                     foaf:givenName ?firstName ;
                     foaf:familyName ?lastName ;
                     rbps:hasAttempt ?attempt .

            ?attempt rdf:type rbps:Attempt;
                     rbps:AttemptCourse ?course;
                     rbps:AttemptGrade ?grade.
            FILTER( ?grade >= 50.0 ) 
        }}
        """
        res = runQuery(query)
        rows = processCSVdata(res.decode('utf-8'))
        if len(rows) == 0:
            dispatcher.utter_message(
                text=f"No students found who passed the course '{course_subject} {course_number}'.")
        else:
            dispatcher.utter_message(
                text=f"Students who passed the course '{course_subject} {course_number}':")
            for row in rows:
                dispatcher.utter_message(
                    text=f"ID: {row[1]}, Name: {row[2]} {row[3]}")
        return []


# Q13
class ActionStudentCourseGrades(Action):
    def name(self):
        return "action_student_course_grades"

    def run(self, dispatcher, tracker, domain):
        student_id = '40182191'
        student_first_name = 'Trenton'
        student_last_name = 'Doyle'

        query = f"""
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rbps: <http://roboprof.com/schema#>

        SELECT ?universityLabel ?courseLabel ?courseSubject ?courseNumber ?grade
        WHERE {{
            ?course rdf:type rbps:Course ;
                    rdfs:label ?courseLabel ;
                    rbps:CourseSubject ?courseSubject ;
                    rbps:CourseOfUniversity ?university ;
                    rbps:CourseNumber ?courseNumber.

            ?university rdfs:label ?universityLabel.

            ?student rdf:type rbps:Student ;
                     rbps:IDNumber "{student_id}"^^xsd:integer;
                     foaf:givenName "{student_first_name}"@en ;
                     foaf:familyName "{student_last_name}"@en ;
                     rbps:hasAttempt ?attempt .

            ?attempt rdf:type rbps:Attempt;
                     rbps:AttemptCourse ?course;
                     rbps:AttemptGrade ?grade.
        }}
        """
        res = runQuery(query)
        rows = processCSVdata(res.decode('utf-8'))
        if len(rows) == 0:
            dispatcher.utter_message(
                text=f"No grades found for student '{student_first_name} {student_last_name}'.")
        else:
            dispatcher.utter_message(
                text=f"Grades for student '{student_first_name} {student_last_name}':")
            for row in rows:
                dispatcher.utter_message(
                    text=f"University: {row[0]}, Course: {row[1]}, Subject: {row[2]}, Number: {row[3]}, Grade: {row[4]}")
        return []
