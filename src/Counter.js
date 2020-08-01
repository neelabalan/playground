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

