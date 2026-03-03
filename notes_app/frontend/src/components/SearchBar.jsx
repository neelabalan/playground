import { useState } from "react";

export default function SearchBar({ setSearchTerm }) {

  const [term, setTerm] = useState("")

  const handleSubmit = (event) => {
    event.preventDefault();
    setSearchTerm(term);
    setTerm("")

  };
  return (
    <form onSubmit={handleSubmit} role="search">
    {/* <form role="search"> */}
        <input
          type="search"
          value={term}
          onChange={(e) => setTerm(e.target.value)}
          placeholder="Search here"
        />
        <button type="submit">Search</button>
    </form>
  );
}
