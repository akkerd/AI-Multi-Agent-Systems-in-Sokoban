"""
    Dictionary with the same behaviour as a matrix
    for space optimization purposes.
    It is NOT thread-safe.
    Author: Jesualdo Garcia Lopez
    Date: 2018/03/27
"""

from collections.abc import MutableMapping


class SparseMatrix(MutableMapping):

    def __init__(self, row: 'int'=None, col: 'int'=None, missing=None, sparse_matrix=None):
        super(MutableMapping, self).__init__()
        self.__tempRow = None
        if sparse_matrix is None:
            self.__maxCol = col
            self.__maxRow = row
            self.store = {}
        else:
            self.store = sparse_matrix.store.copy()
            self.__maxCol = sparse_matrix.columns
            self.__maxRow = sparse_matrix.rows

    def __getitem__(self, *key):
        if key.__len__() == 1:
            key = key[0]
            if self.__tempRow is None:
                if self.__maxRow is not None and key >= self.__maxRow:
                    raise IndexError()
                else:
                    self.__tempRow = key
                    return self
            else:
                if self.__maxCol is not None and key >= self.__maxCol:
                    raise IndexError()
                else:
                    temp = self.__tempRow  # This is here in order to make sure that self.__tempRow is cleared
                    self.__tempRow = None
                    result = self.store.get((temp, key))
                    return result
        else:
            return self.store.get(key)

    def __setitem__(self, key, value):
        if self.__tempRow is not None:
            if self.__maxCol is not None and key >= self.__maxCol:
                raise IndexError()
            else:
                temp = self.__tempRow  # This is here in order to make sure that self.__tempRow is cleared
                self.__tempRow = None
                if value is None:
                    del self.store[(temp, key)]
                else:
                    self.store[(temp, key)] = value

    def __delitem__(self, key):
        if self.__tempRow is not None:
            if key >= self.__maxCol:
                raise IndexError()
            else:
                temp = self.__tempRow  # This is here in order to make sure that self.__tempRow is cleared
                self.__tempRow = None
                del self.store[(temp, key)]

    def __len__(self):
        return len(self.store)

    def __repr__(self):
        return self.store.__repr__()

    def __iter__(self):
        return iter(self.store)

    def items(self):
        return self.store.items()

    def __hash__(self):
        return hash(frozenset(self.store.items()))

    @property
    def columns(self):
        return self.__maxCol

    @columns.setter
    def columns(self, value):
        self.__maxCol = value

    @property
    def rows(self):
        return self.__maxRow

    @rows.setter
    def rows(self, value):
        self.__maxRow = value


if __name__ == '__main__':
    sparseMatrix = SparseMatrix(10, 5)
    sparseMatrix[1][3] = 'a'
    sparseMatrix[4][2] = 'h'
    sparseMatrix[4][1] = 'a'

    print(sparseMatrix)

    for i in range(0, 10):
        for j in range(0, 5):
            print("\t" + str(sparseMatrix[i][j]), end='')
        print("\n")

    for i in sparseMatrix:
        print(i)
