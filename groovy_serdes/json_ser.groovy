import com.fasterxml.jackson.databind.ObjectMapper
import model

def related1 = new model.Relation(relationship="friend", age=40)
def related2 = new model.Relation(relationship="co-worker", age=45)
def person = new model.Person(name="John Doe", age=30, relations=[related1, related2])

def mapper = new ObjectMapper()
def json = mapper.writeValueAsString(person)
println json
