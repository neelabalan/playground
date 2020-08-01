import { createMuiTheme } from "@material-ui/core"
import { lightBlue } from "@material-ui/core/colors";
import { dark } from "@material-ui/core/styles/createPalette";

export const darkTheme = createMuiTheme({
	palette: {
		type: 'dark',
		primary: {
			main: lightBlue[500]
		},
		secondary: {
			main: '#42a5f5',
		},
		background: {
			default: '#000',
			paper: '#000'
		},
	}
})

export const lightTheme = createMuiTheme({
	pallete: {
		primary: {
			main: lightBlue[500]
		},
		secondary: {
			main: '#42a5f5',
		},
	}
})




