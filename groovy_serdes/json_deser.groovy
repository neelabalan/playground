import com.fasterxml.jackson.databind.ObjectMapper
import model

ObjectMapper mapper = new ObjectMapper()
model.Person person = mapper.readValue(new File('person.json'), model.Person.class)

assert person.age == 40
assert person.relation[0].age == 40