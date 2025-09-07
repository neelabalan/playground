module Main where

import Freq (freqWithEnvelope, play, save, wave)
import Options.Applicative
import Rule110 (applyRule, randomCellList)
import Util (binaryToDecimal, groupedSeq3)

data Args = Args
  { durationArg :: Float,
    startArg :: Float,
    stopArg :: Float,
    stepArg :: Float,
    repeatArg :: Int
  }
  deriving (Show)

argsInfo :: ParserInfo Args
argsInfo =
  info
    (argsParser <**> helper)
    ( fullDesc
        <> progDesc "Parse command-line arguments for length, duration, start, stop, and step"
        <> header "Argument Parser Example"
    )

argsParser :: Parser Args
argsParser =
  Args
    <$> option
      auto
      ( long "duration"
          <> short 'd'
          <> metavar "FLOAT"
          <> help "Duration in seconds"
      )
    <*> option
      auto
      ( long "start"
          <> short 's'
          <> metavar "FLOAT"
          <> help "Start value"
      )
    <*> option
      auto
      ( long "stop"
          <> short 't'
          <> metavar "FLOAT"
          <> help "Stop value"
      )
    <*> option
      auto
      ( long "step"
          <> short 'p'
          <> metavar "FLOAT"
          <> help "Step size"
      )
    <*> option
      auto
      ( long "repeat"
          <> short 'r'
          <> metavar "INT"
          <> help "Times to repeat the sequence"
      )

outputFilePath :: FilePath
outputFilePath = "output.bin"

main :: IO ()
main = do
  putStrLn "Hello, Haskell!"
  args <- execParser argsInfo
  putStrLn $ "Parsed arguments: " ++ show args
  let start = startArg args
  let stop = stopArg args
  let step = stepArg args

  let freqRange = [start, start + step .. stop]
  randomInitialSeq <- randomCellList 30 -- just a random number
  let indices = map binaryToDecimal $ groupedSeq3 $ applyRule randomInitialSeq
  print indices
  let frequencies = [freqRange !! i - 1 | i <- indices]
  print frequencies
  let wave = concat $ replicate (repeatArg args) $ foldMap freqWithEnvelope frequencies (durationArg args)
  _ <- save wave outputFilePath
  play outputFilePath

  -- let pulse = wave (startArg args) (stopArg args) (stepArg args) (durationArg args)
  -- _ <- save pulse outputFilePath
  -- play outputFilePath

  return ()