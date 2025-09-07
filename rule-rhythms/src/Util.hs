module Util where

import Data.List.Split (chunksOf)
import Rule110 (Cell (Empty, Filled))

cellToNumber :: Cell -> Int
cellToNumber Empty = 0
cellToNumber Filled = 1

groupedSeq :: Int -> [Cell] -> [[Int]]
groupedSeq range cells = chunksOf range $ map cellToNumber cells

groupedSeq3 :: [Cell] -> [[Int]]
groupedSeq3 cells = groupedSeq 3 cells

groupedSeq5 :: [Cell] -> [[Int]]
groupedSeq5 cells = groupedSeq 5 cells

binaryToDecimal :: [Int] -> Int
binaryToDecimal bits = sum $ zipWith (\bit power -> bit * (2 ^ power)) (reverse bits) [0 .. length bits - 1]