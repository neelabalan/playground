import React, { useState, useEffect } from 'react'
import IconButton from '@material-ui/core/IconButton'
import AddCircleRoundedIcon from '@material-ui/icons/AddCircleRounded';
import RemoveCircleRoundedIcon from '@material-ui/icons/RemoveCircleRounded';
import ReplayIcon from '@material-ui/icons/Replay';
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

export default function Counter() {

	const [count, setCount] = useState(0)
	useEffect(() =>{
		document.addEventListener("keydown", handleKeyDown, false)

		return () => {
			document.removeEventListener("keydown", handleKeyDown, false)
		}
	})


	const increment = () => setCount(count + 1)
	const decrement = () => {
		if (count > 0) {
			setCount(count - 1)
		}
	}
	const reset = () => setCount(0)

	const handleKeyDown = (event) => {
		if (event.keyCode === 75) {
			increment()
		}
		if (event.keyCode === 74) {
			decrement()
		}
		if (event.keyCode === 27) {
			reset()
		}
	}

	return (
		<div>
			<Grid>
				<h1 style={styles.header} >{count}</h1>
			</Grid>
			<Grid style={styles.buttons} container direction="row" justify="center" alignItems="center">
				<Grid item xs style={{ textAlign: 'center' }}>
					<IconButton onClick={increment}>
						<AddCircleRoundedIcon style={styles.largeButton} />
					</IconButton>
				</Grid>

				<Grid item xs style={{ textAlign: 'center' }}>
					<IconButton textAlign='center' onClick={decrement}>
						<RemoveCircleRoundedIcon style={styles.largeButton} />
					</IconButton>

				</Grid>

				<Grid item xs style={{ textAlign: 'center' }}>
					<IconButton onClick={reset}>
						<ReplayIcon style={styles.largeButton} />
					</IconButton>
				</Grid>

			</Grid>
		</div>
	)

}
