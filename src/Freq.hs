module Freq where

import Data.ByteString.Builder qualified as Bl
import Data.ByteString.Lazy qualified as B
import System.Process
import Text.Printf (printf)

-- https://www.sonarworks.com/blog/learn/sample-rate
sampleRate :: Float
sampleRate = 48000.0

type Hz = Float

type Seconds = Float

type Pulse = Float

freq :: Hz -> Seconds -> [Pulse]
freq hz duration =
  map (sin . (* step)) [0.0 .. sampleRate * duration]
  where
    step = (hz * 2 * pi) / sampleRate

freqWithEnvelope :: Hz -> Seconds -> [Pulse]
freqWithEnvelope hz duration =
  zipWith (*) envelope sineWave
  where
    numSamples = sampleRate * duration
    sineWave = freq hz duration
    -- 10 ms
    attackSamples = 0.01 * sampleRate
    decaySamples = 0.01 * sampleRate
    sustainLevel = 1.0
    envelope :: [Pulse]
    envelope =
      [i / attackSamples | i <- [0.0 .. attackSamples - 1]]
        ++ replicate  (round (numSamples - attackSamples - decaySamples)) sustainLevel
        ++ [sustainLevel * (1.0 - i / decaySamples) | i <- [0.0 .. decaySamples - 1]]

wave :: Float -> Float -> Float -> Float -> [Pulse]
wave start stop step duration = foldMap freqWithEnvelope [start, start+step .. stop] duration

save :: [Pulse] -> FilePath -> IO ()
save pulses filePath = B.writeFile filePath $ Bl.toLazyByteString $ foldMap Bl.floatLE pulses

play :: FilePath -> IO ()
play outputFilePath = do
  --   _ <- runCommand $ printf "ffplay -showmode 1 -f f32le -ar %f %s" sampleRate outputFilePath
  _ <- runCommand $ printf "ffplay -f f32le -ar %f %s" sampleRate outputFilePath 
  return ()