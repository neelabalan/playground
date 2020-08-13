import { CssBaseline } from "@material-ui/core"
import { lightTheme, darkTheme } from "./theme"
import IconButton from '@material-ui/core/IconButton'
import Grid from '@material-ui/core/Grid'
import Counter from "./Counter"
// light theme 
import Brightness5Icon from '@material-ui/icons/Brightness5'

// dark theme
import Brightness2Icon from '@material-ui/icons/Brightness2';
import { ThemeProvider } from "@material-ui/styles";
import React, { useState } from 'react';


export default function App() {
	const [isDarkTheme, setDarkTheme] = useState(false)
	const toggleTheme = () => {
		setDarkTheme(!isDarkTheme)
	}

	return (
		<ThemeProvider theme={isDarkTheme ? darkTheme : lightTheme} >
			<CssBaseline />
			<Grid container justify="flex-end">
				<IconButton onClick={toggleTheme}>
					{isDarkTheme ? <Brightness5Icon style={{ fontSize: '50px' }} /> : <Brightness2Icon style={{ fontSize: '50px' }} />}
				</IconButton>
			</Grid>
			<Counter />
		</ThemeProvider>
	)
}
