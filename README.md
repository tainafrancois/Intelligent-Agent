# Roboprof Intelligent Agent

## Prerequisites

- The project is set up to run with **Python 3.6**

- To avoid conflicts between this Python version and your current version, use a conda environment:

1. You will need to install Anaconda from:
   https://docs.anaconda.com/anaconda/install/
2. Create a conda environment with Python 3.6 from:

https://docs.anaconda.com/anaconda/install/ 2. Create a conda environment with Python 3.10 from:

```
conda create --name Roboprof python=3.10
```

3. Activate comp474 from:

4. Activate Roboprof from:

```
conda activate Roboprof
```

4. Make sure that the Python version within your environment is 3.6 from:

```
python -V
```

## Getting Started

1. You need to install dependencies for the project from:

```
pip install -r requirements.txt
```

2. Create the knowledge base from:

```
python create_knowledge_base.py
```

3. Start Apache Fuseki server, which will listen for requests on port 3030

4. Access Fuseki's web interface by navigating to http://localhost:3030/ in your browser

5. Select the 'manage' tab

6. Select the 'new dataset' tab

7. Create a dataset named **Roboprof**

8. Under the 'existing datasets' tab, select **Roboprof** dataset

9. Select 'add data' button

10. Select 'select files' button

11. Select 'Vocabulary.ttl' and 'Knowledge_Base.ttl'

12. Select 'upload all' button to upload 'Vocabulary.ttl' and 'Knowledge_Base.ttl'

13. Now the SPARQL server is ready to query

14. Go to the 'query' tab to start querying

After uploading “Knowledge_Base.ttl” and “Vocabulary.ttl” to the SPARQL server, you can execute Statistics queries about the Knowledge Base and 13 given queries from:

```
python main.py
```

All output files are stored in _/outputs_ folder

## Running the Chatbot:

- Navigate to the `roboprof` directory.
- Train the Rasa model using the command rasa train.
- Start the Rasa server using the command rasa run --enable-api.
- Interact with the chatbot through the Rasa REST API.
