import React from 'react'
import IconButton from '@material-ui/core/IconButton'
import AddCircleRoundedIcon from '@material-ui/icons/AddCircleRounded';
import RemoveCircleRoundedIcon from '@material-ui/icons/RemoveCircleRounded';
import ReplayIcon from '@material-ui/icons/Replay';
import { makeStyles } from '@material-ui/core/styles';
import Grid from '@material-ui/core/Grid';

const styles = {
	largeButton: {
		fontSize: '150px',
	},
	header: {
		textAlign: 'center',
		fontFamily: 'Roboto Mono, monospace',
		fontSize: '200px'
	},
	buttons: {
		alignContent: 'center',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
	}
}
export default class Counter extends React.Component {

	state = {
		count: 0 
	};

	increment = () => {
		this.setState({
			count: this.state.count + 1
		});
	};

	decrement = () => {
		if (this.state.count > 0) {
			this.setState({
				count: this.state.count - 1
			});
		}
	};
	reset = () => {
		this.setState({
			count: 0
		})
	}

	handleKeyDown = (event) => {
		if (event.keyCode === 75) {
			this.increment()
		}
		if (event.keyCode === 74) {
			this.decrement()
		}
		if (event.keyCode === 27) {
			this.reset()
		}
	}

	componentDidMount() {
		document.addEventListener("keydown", this.handleKeyDown, false);
	}

	render() {
		return (

			<div>
				<Grid>
					<h1 style={styles.header} >{this.state.count}</h1>
				</Grid>
				<Grid style={styles.buttons} container direction="row" justify="center" alignItems="center">
					<Grid item xs style={{textAlign : 'center'}}>
						<IconButton onClick={this.increment}>
							<AddCircleRoundedIcon style={styles.largeButton} />
						</IconButton>
					</Grid>

					<Grid item xs style={{textAlign : 'center'}}>
						<IconButton textAlign='center' onClick={this.decrement}>
							<RemoveCircleRoundedIcon style={styles.largeButton} />
						</IconButton>
		
					</Grid>

					<Grid item xs style={{textAlign : 'center'}}>
						<IconButton onClick={this.reset}>
							<ReplayIcon style={styles.largeButton} />
						</IconButton>
					</Grid>

				</Grid>
			</div>
		)
	}
}




// const useStyles = makeStyles((theme) => ({
//   root: {
//     flexGrow: 1,
//   },
//   paper: {
//     height: 140,
//     width: 100,
//   },
//   control: {
//     padding: theme.spacing(2),
//   },
// }));

// export default function SpacingGrid() {
//   const [spacing, setSpacing] = React.useState(2);
//   const classes = useStyles();

//   const handleChange = (event) => {
//     setSpacing(Number(event.target.value));
//   };

// return (
// 	<Grid container className={classes.root} spacing={2}>
// 		<Grid item xs={12}>
// 			<Grid container justify="center" spacing={spacing}>
// 				{[0, 1, 2].map((value) => (
// 					<Grid key={value} item>
// 						<Paper className={classes.paper} />
// 					</Grid>
// 				))}
// 			</Grid>
// 		</Grid>
// 		<Grid item xs={12}>
// 			<Paper className={classes.control}>
// 				<Grid container>
// 					<Grid item>
// 						<FormLabel>spacing</FormLabel>
// 						<RadioGroup
// 							name="spacing"
// 							aria-label="spacing"
// 							value={spacing.toString()}
// 							onChange={handleChange}
// 							row
// 						>
// 							{[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((value) => (
// 								<FormControlLabel
// 									key={value}
// 									value={value.toString()}
// 									control={<Radio />}
// 									label={value.toString()}
// 								/>
// 							))}
// 						</RadioGroup>
// 					</Grid>
// 				</Grid>
// 			</Paper>
// 		</Grid>
// 	</Grid>
// );
// }
