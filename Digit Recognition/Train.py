__author__ = 'bdwalker'
import pickle
import numpy as np
import SVM
import Kernels
import sys
import multiprocessing.pool as mp
import multiprocessing
import Perceptron


class Trainer:
    processed_data = None

    def _loadProcessedData(self, input_file):
        inputf = open(input_file, "r")
        self.processed_data = pickle.load(inputf)

    # Separate data into buckets, keyed by the label
    def processData(self, raw_data, output_file=None, input_file=None):
        train_data = None
        if input_file is None:
            if output_file is not None:
                output = open(output_file, "w+")

            print "***** Separating Data Into Classes..."
            train_data = self._loadClasses(raw_data)

            # serialize
            if output_file is not None:
                print "***** Serializing Data to %s" % output_file
                pickle.dump(train_data, output)

        else:
            print "***** Loading Data From %s" % input_file
            inputf = open(input_file, "r")
            train_data = pickle.load(inputf)

        print "***** Combining Classes for Training"
        self.processed_data = self._combineClasses(train_data)

        print "***** Processing Data Complete"

    def _loadClasses(self, raw_data):
        train_data = dict()
        for row in raw_data:
            label = row[0]
            if label in train_data.keys():
                current = np.atleast_2d(train_data[label])
                row = np.atleast_2d(row)
                train_data[label] = np.vstack((current, row))
            else:
                train_data[label] = row

        print len(train_data)
        return train_data

    def _combineClasses(self, train_data):
        pairings = dict()
        for key1 in train_data.keys():
            class1 = train_data[key1]
            class1[:, 0] = 1
            for key2 in train_data.keys():
                if key2 > key1:
                    class2 = train_data[key2]
                    class2[:, 0] = -1
                    combined = np.vstack((class1, class2))

                    # rows need to be shuffled, otherwise not i.i.d
                    np.random.shuffle(combined)
                    pairings[(key1, key2)] = combined
        return pairings

    def trainModel(self, kernel=Kernels.defaultKernel, report=False, plot=False, output=None):
        if self.processed_data is None:
            print "Training data has not been loaded! \n " \
                  "Must load data with a call to processData or loadProcessedData."
            sys.exit(1)

        # go get some lunch, this is gonna take some time
        threads = dict()
        cores = multiprocessing.cpu_count()
        pool = mp.ThreadPool(processes=cores)

        #trained_model = dict()
        for couple in self.processed_data.keys():
            arg = (self.processed_data[couple], kernel, report, plot)
            result = pool.apply_async(self._trainSingleClass, arg)
            threads[couple] = result
            #trained_model[couple] = self._trainSingleClass(self.processed_data[couple], kernel, report, plot)

        pool.close()
        pool.join()

        trained_model = dict()
        for r in threads.keys():
            thread = threads[r]
            trained_model[r] = thread.get()
        #     #Stored length 785

        perceptron = Perceptron.Classifier()
        model = perceptron.packModel(trained_model)
        #serialize trained model

        if output is not None:
            out = open(output, "w+")
            pickle.dump(model, out)

    def _trainSingleClass(self, data, kernel, report, plot):
        perceptron = Perceptron.Classifier()
        return perceptron.trainModel(data, kernel, report)









