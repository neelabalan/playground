import argparse

import numpy as np


def count_singular_matrices(num_matrices: int, min_dim: int, max_dim: int) -> int:
    singular_count = np.sum(
        [
            np.linalg.det(np.random.rand(dim, dim)) == 0
            for _ in range(num_matrices)
            for dim in range(min_dim, max_dim + 1)
        ]
    )
    return singular_count


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Count the number of singular matrices.')
    parser.add_argument('--num_matrices', type=int, required=True, help='The number of matrices to generate.')
    parser.add_argument('--min_dim', type=int, required=True, help='The minimum dimension of the matrices.')
    parser.add_argument('--max_dim', type=int, required=True, help='The maximum dimension of the matrices.')
    args = parser.parse_args()

    singular_count = count_singular_matrices(args.num_matrices, args.min_dim, args.max_dim)
    print(f'Number of singular matrices: {singular_count}')
