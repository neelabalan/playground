import ThoughtCard from "./ThoughtCard";

export default function ThoughtList({ searchTerm, thoughts, handleDelete }) {
  var filteredThoughts = thoughts
  if (searchTerm !== "") {

    // Filter thoughts based on the search term
    filteredThoughts = filteredThoughts.filter(thought => 
      thought.note.toLowerCase().includes(searchTerm.toLowerCase())
    );
    console.log(filteredThoughts)

  }
  return filteredThoughts.map(thought => {
      return <ThoughtCard
        key={thought.id}
        thought={thought}
        handleDelete={handleDelete}
      />
  });
}
