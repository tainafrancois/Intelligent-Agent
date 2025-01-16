from SPARQLWrapper import SPARQLWrapper, CSV, JSON
from os import listdir
import os.path

def runQuery(query, format=CSV):
    sparql = SPARQLWrapper("http://localhost:3030/Roboprof/query")
    sparql.setReturnFormat(format)
    sparql.setQuery(query)
    try:
        ret = sparql.queryAndConvert()
        return ret
    except Exception as e:
        print(e)

def runQueryFiles():
    queriesDir = os.path.join('./queries/')
    for queryFile in listdir(queriesDir):
        queryNum = queryFile[0:queryFile.find('.')] 
        with open(os.path.join(queriesDir,queryFile), 'r') as file:
            query = f'''{file.read()}'''
            result = runQuery(query)
            with open(os.path.join('./outputs/','.'.join(['-'.join([queryNum, 'out']),'csv'])),'wb') as file:
                file.write(result)


def deriveKBStatistics():
    path = os.path.join('outputs','KBStatistics.txt')
    # Delete KBStatistics.txt if it exists
    try:
        os.remove(path)
    except OSError:
        pass

    with open(path, 'a') as file:
            
        totalTriplesQuery = '''
            SELECT (COUNT(*) as ?NumberOfTriples)
            WHERE { 
                ?subject ?predicate ?object . 
            }
        '''
        ret = runQuery(totalTriplesQuery, JSON)

        file.write(f"Total triples in the knowledge base is: {ret['results']['bindings'][0]['NumberOfTriples']['value']}")

        totalCoursesQuery = '''
            Prefix rbps: <http://roboprof.com/schema#>

            SELECT (COUNT(?course) as ?NumberOfCourses)
            WHERE { ?course a rbps:Course . }
        '''
        ret = runQuery(totalCoursesQuery, JSON)

        file.write(f"\nTotal courses in the knowledge base is: {ret['results']['bindings'][0]['NumberOfCourses']['value']}")

        totalTopicQuery = '''
            Prefix rbps: <http://roboprof.com/schema#>

            SELECT (COUNT(?topic) as ?NumberOfTopics)
            WHERE { ?topic a rbps:Topic . }
        '''
        ret = runQuery(totalTopicQuery, JSON)

        file.write(f"\nTotal topics in the knowledge base is: {ret['results']['bindings'][0]['NumberOfTopics']['value']}")

    
def main():
    if not os.path.exists('outputs'):
        os.makedirs('outputs')
    deriveKBStatistics()
    runQueryFiles()


if __name__ == "__main__":
    main()
