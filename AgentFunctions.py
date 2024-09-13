from openai import OpenAI
import os
class SingletonMeta(type):
    """
    A Singleton metaclass that ensures a class has only one instance.
    """
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class AgentsHub(metaclass=SingletonMeta):
    tableName = 'properties_property'
    def __init__(self):
        """
        Initializes an instance of the AgentsHub class.

        This method loads environment variables from a .env file, retrieves the API key from the environment variables,
        and initializes the OpenAI client using the API key. It also retrieves the RealEstateAttorney assistant from the
        OpenAI client.
        """
        apiKey=os.environ.get("OPENAI_API_KEY")
        self.client= OpenAI(api_key=apiKey)
        self.scriptWriter = self.client.beta.assistants.retrieve('asst_yLbW8Y9evJaDLFWIiK9NPVqs')

    def getClient(self):
        return self.client
    
    def getscriptWriter(self):
        return self.scriptWriter
    


def createThread():
    agenthub=AgentsHub()
    client=agenthub.getClient()
    thread = client.beta.threads.create()
    return thread

def executeBasicAgent(assistant, threadId, query=None):
    agenthub=AgentsHub()
    client=agenthub.getClient()
    if query!=None:
        message = client.beta.threads.messages.create(
            thread_id=threadId,
            role="user",
            content=query
        )
        
    run = client.beta.threads.runs.create(
        thread_id=threadId,
        assistant_id=assistant.id,
    )

    while True:
        # time.sleep(2)
        run_status = client.beta.threads.runs.retrieve(
            thread_id=threadId,
            run_id=run.id
        )
        if run_status.status == 'completed':
            messages = client.beta.threads.messages.list(
                thread_id=threadId
            )

            # Loop through messages and print content based on role
            for msg in messages.data:
                role = msg.role
                content = msg.content[0].text.value
                return content
            
        elif run_status.status=='failed' or run_status.status=='cancelled':
            return 'Failed'