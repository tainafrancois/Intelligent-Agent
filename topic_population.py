
# import parser object from tike 
from tika import parser   
from os import listdir
import os.path

def parseFileToText(fileName, path):
    # Convert Course outline to text
    parsed_pdf = parser.from_file(os.path.join(path,fileName).replace('\\','/')) 
    
    # saving content of pdf 
    data = parsed_pdf['content']
    txtFile = '.'.join([fileName.split('.')[0],"txt"])
    with open(os.path.join(path,txtFile), "w", encoding='utf-8') as file:
           file.write(data)

def populate_topics(courseName):
    coursePath = os.path.join('./courses/', courseName)
    for dir in listdir(coursePath):
        dirPath = os.path.join(coursePath, dir)
        # Convert Course outline to text
        if (os.path.isdir(dirPath)):
                for file in sorted(listdir(dirPath)):
                    parseFileToText(file,dirPath)
        else:
             parseFileToText(dir,coursePath)
populate_topics('COMP474')
populate_topics('COMP445')