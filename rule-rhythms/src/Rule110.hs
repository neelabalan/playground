module Rule110 where

import System.Random

data Cell = Empty | Filled deriving (Eq, Show)

randomCell :: IO Cell
randomCell = do
    n <- randomRIO (0 :: Int, 1)
    return $ if n == 0 then Empty else Filled

randomCellList :: Int -> IO [Cell]
randomCellList n = sequence $ replicate n randomCell

rule :: Cell -> Cell -> Cell -> Cell
rule Filled Filled Filled = Empty
rule Filled Filled Empty = Filled
rule Filled Empty Filled = Filled
rule Filled Empty Empty = Empty
rule Empty Filled Filled = Filled
rule Empty Filled Empty = Filled
rule Empty Empty Filled = Filled
rule Empty Empty Empty = Empty

applyRule :: [Cell] -> [Cell]
applyRule (x : y : z : xs) = rule x y z : applyRule (y : z : xs)
applyRule _ = []
