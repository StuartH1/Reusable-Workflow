import numpy as np

def test_numpy_operations():
    # Create a 1D NumPy array
    one_dimensional_array = np.array([1.2, 2.4, 3.5, 4.7, 6.1, 7.2, 8.3, 9.5])
    print(one_dimensional_array)

    two_dimensional_array = np.array([[6, 5], [11, 7], [4, 8]])
    print(two_dimensional_array)

    sequence_of_integers = np.arange(5, 12)
    print(sequence_of_integers)  # output excludes the specified end value

    random_integers_between_50_and_100 = np.random.randint(low=50, high=101, size=(6,))
    print(random_integers_between_50_and_100)
    random_integers_between_50_and_100 = random_integers_between_50_and_100 + 7
    print(random_integers_between_50_and_100)

    # Linear Data Set
    print("Linear Data Set")
    feature = np.arange(start=6, stop=21, step=1)
    print(feature)
    label = feature * 3 + 4
    print(label)

if __name__ == "__main__":
    test_numpy_operations()