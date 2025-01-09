import com.fasterxml.jackson.annotation.JsonCreator
import com.fasterxml.jackson.annotation.JsonProperty

class model {
    static class Relation {
        String relationship
        Integer age

        @JsonCreator(model = JsonCreator.Mode.PROPERTIES)
        Relation(@JsonProperty("relationship") String relationship, @JsonProperty("age") Integer age) {
            this.relationship = relationship
            this.age = age
        }
    }

    static class Person {
        String name
        Integer age
        List<Relation> relations

        @JsonCreator(model = JsonCreator.Mode.PROPERTIES)
        Person(@JsonProperty("name") String name, @JsonProperty("age") Integer age, @JsonProperty("relations") List<Relation> relations) {
            this.name = name
            this.age = age
            this.relations = relations
        }
    }
}