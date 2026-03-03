import { useContext } from "react";
import NavigationContext from "../provider/NavigationContext";

// just a wrapper for clarity
export default function useNavigation() {
    return useContext(NavigationContext)
}