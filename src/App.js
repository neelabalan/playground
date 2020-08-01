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
import React from 'react';


export default class App extends React.Component {
	constructor(props) {
		super(props)
		this.state = {
			isDarkTheme: false,
		}
	}

	toggleTheme = () => {
		this.setState({
			isDarkTheme: !this.state.isDarkTheme,
		})
	}

	render() {
		return (
			<ThemeProvider theme={this.state.isDarkTheme ? darkTheme : lightTheme} >
				<CssBaseline />
				<Grid container justify="flex-end">
					<IconButton onClick={this.toggleTheme}>
						{this.state.isDarkTheme ? <Brightness5Icon style={{fontSize:'50px'}}/> : <Brightness2Icon style={{fontSize:'50px'}}/>}
					</IconButton>
				</Grid>
				<Counter />
			</ThemeProvider>
		);
	}
}
