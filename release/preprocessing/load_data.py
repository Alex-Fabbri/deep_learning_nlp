# using the following for reference:
# https://github.com/umass-semeval/semeval16/blob/master/semeval/lstm_words.py 
import cPickle
import numpy as np
from collections import defaultdict, OrderedDict
import theano
import theano.tensor as T
import re
import warnings
import sys
import pandas as pd
import logging
import math
import pickle
import os
import timeit
import time
import lasagne
from lasagne.layers import get_output_shape
from release.preprocessing.process_properties import PreProcessor
from release.preprocessing.utils import str_to_bool 

def load_data(target,config_file):

    processor = PreProcessor(config_file)
    return_dict = processor.__dict__
    path = processor.output
    both = str_to_bool(processor.both)
    top = str_to_bool(processor.topSim)
    batch_size = int(processor.batch_size)


    # get the train and validation data 
    if both == False:
        train_file = path + '/pkl/1_cnn/w2v_300/' + 'ucsc.nocontext.TRAIN.' +   target  + '.pkl'
        test_file = path + '/pkl/1_cnn/w2v_300/' + 'ucsc.nocontext.TEST.' + target +  '.pkl'
    
    if both == True:
        train_file = path + '/pkl/1_cnn/w2v_300/' + 'ucsc.contextcat.TRAIN.' +   target  + '.pkl'
        test_file = path + '/pkl/1_cnn/w2v_300/' + 'ucsc.contextcat.TEST.' + target +  '.pkl'

        
    if both == True and top == True:
        train_file = path + '/pkl/1_cnn/w2v_300/' + 'ucsc.contexttop.TRAIN.' +   target  + '.pkl'
        test_file = path + '/pkl/1_cnn/w2v_300/' + 'ucsc.contexttop.TEST.' + target +  '.pkl'
    
    print "loading data...",
    #logger.error("loading data...");
    
    x = cPickle.load(open(train_file,"rb"))
    train_data, W, word_idx_map, max_l = x[0], x[1], x[2], x[3]
    return_dict["W"] = W
    # print(word_idx_map['i'])
    # print(word_idx_map['the'])
    # print(train_data[0])
    #print(word_idx_map)
    X_train_indx, y_train = text_to_indx(train_data, word_idx_map)
    X_train, X_train_mask = pad_mask(X_train_indx, max_l)
    return_dict["max_seq_len"] = max_l

    # print(X_train_indx[0])
    # print(len(X_train_indx[0]))
    
    # print(X_train[0])
    # print(X_train_mask[0])
    # print(sum(X_train_mask[0]))
    # print("SUMMED")
    #train_data = np.asarray(train_data)


    #print("\n train_data.shape: {}\n".format(train_data.shape))
    #n_batches = int(math.ceil(train_data.shape[0]/float(batch_size)))
    #n_train_batches = int(np.round(n_batches*0.9))
    ## print(n_batches)
    ## print(n_train_batches)
    ## print 'n_batches: ', n_batches
    ## print 'n_train_batches: ', n_train_batches
    #train_set_x = X_train[:n_train_batches*batch_size,:]
    #train_set_mask = X_train_mask[:n_train_batches*batch_size,:]
    #train_set_y = y_train[:n_train_batches*batch_size]

    #print 'train_set_x.shape: ', train_set_x.shape
    #val_set_x = X_train[n_train_batches*batch_size:,:]
    #val_set_mask = X_train_mask[n_train_batches*batch_size:,:]
    #val_set_y = y_train[n_train_batches*batch_size:]

    #print 'val_set_x: ', val_set_x.shape
    #if val_set_x.shape[0] % batch_size > 0:
    #    #print("shape doesn't match\n")
    #    extra_data_num = batch_size - val_set_x.shape[0] % batch_size
    #    new_set = np.append(val_set_x, val_set_x[:extra_data_num], axis=0)
    #    new_set_mask = np.append(val_set_mask, val_set_mask[:extra_data_num], axis = 0)
    #    new_set_y = np.append(val_set_y, val_set_y[:extra_data_num], axis = 0)
    #    # might be possible that we still do not have the proper batch size - 
    #    # in that case - for remaining - add from "training" data
    #    val_set_x = new_set
    #    val_set_mask = new_set_mask
    #    val_set_y = new_set_y
    #    if val_set_x.shape[0] % batch_size > 0:
    #         extra_data_num = batch_size - val_set_x.shape[0] % batch_size
    #         new_set = np.append(val_set_x, train_set_x[:extra_data_num], axis=0)
    #         new_set_mask = np.append(val_set_mask, train_set_mask[:extra_data_num], axis = 0)
    #         new_set_y = np.append(val_set_y, train_set_y[:extra_data_num], axis = 0)

    #         val_set_x = new_set
    #         val_set_mask = new_set_mask
    #         val_set_y = new_set_y
    ##print 'val_set_x after adjustment: ', val_set_x.shape
    #print 'train size =', train_set_x.shape, ' val size after adjustment =', val_set_x.shape 

    # get the test data

    test_data = cPickle.load(open(test_file,'rb'))
    X_test_indx, y_test = text_to_indx(test_data, word_idx_map)
    X_test, X_test_mask = pad_mask(X_test_indx, max_l)
    # print(test_data[0]['text'])
    # print(X_test_indx[0])
    # print(X_test[0])
    # print(X_test_mask[0])

    # put into shared variables  -- only useful if using GPU
    # move somewhere else
    #train_set_x, train_set_mask, train_set_y = shared_dataset_mask(X_train, X_train_mask, y_train)
    #test_set_x, test_set_mask, test_set_y = shared_dataset_mask(X_test, X_test_mask, y_test)
    train_set_x, train_set_mask, train_set_y = X_train, X_train_mask, y_train
    test_set_x, test_set_mask, test_set_y = X_test, X_test_mask, y_test


    print "data loaded!"
    
    print "max length = " + str(max_l)
    training = np.array(zip(*[train_set_x, train_set_mask]))
    y = np.asarray(train_set_y)

    testing = np.array(zip(*[test_set_x, test_set_mask]))
    test_y = np.asarray(test_set_y)

    return training,y,testing,test_y,return_dict

def text_to_indx(train_data, word_idx_map):
    X = []
    y = []
    for query in train_data:
        text = query["text"].split()
        y_val = query["y"]
        out = []
        for word in text:
            if word in word_idx_map:
                out.append(word_idx_map[word])
            else:
                # unknown word
                out.append(1)
        X.append(out)
        y.append(y_val)
    return X,y

def pad_mask(X_train_indx, max_l):

    N = len(X_train_indx)
    X = np.zeros((N, max_l), dtype=np.int32)
    X_mask = np.zeros((N,max_l), dtype = np.int32)
    for i, x in enumerate(X_train_indx):
        n = len(x)
        if n < max_l:
            X[i, :n] = x
            X_mask[i, :n] = 1
        else:
            X[i, :] = x[:max_l]
            X_mask[i, :] = 1

    return X,X_mask


def shared_dataset(data_xy, borrow=True):
        """ Function that loads the dataset into shared variables

        The reason we store our dataset in shared variables is to allow
        Theano to copy it into the GPU memory (when code is run on GPU).
        Since copying data into the GPU is slow, copying a minibatch everytime
        is needed (the default behaviour if the data is not in a shared
        variable) would lead to a large decrease in performance.
        """
        data_x, data_y = data_xy
        shared_x = theano.shared(np.asarray(data_x,
                                               dtype=theano.config.floatX),
                                 borrow=borrow)
        shared_y = theano.shared(np.asarray(data_y,
                                               dtype=theano.config.floatX),
                                 borrow=borrow)
        return T.cast(shared_x, 'int32'), T.cast(shared_y, 'int32')

def shared_dataset_mask(data_x,data_y, data_z, borrow=True):
        """ Function that loads the dataset into shared variables

        The reason we store our dataset in shared variables is to allow
        Theano to copy it into the GPU memory (when code is run on GPU).
        Since copying data into the GPU is slow, copying a minibatch everytime
        is needed (the default behaviour if the data is not in a shared
        variable) would lead to a large decrease in performance.
        """

        shared_x = theano.shared(np.asarray(data_x,
                                                 dtype=theano.config.floatX),
                                 borrow=borrow)
        shared_y = theano.shared(np.asarray(data_y,
                                               dtype=theano.config.floatX),
                                 borrow=borrow)
        shared_z = theano.shared(np.asarray(data_z,
                                                 dtype=theano.config.floatX),
                                 borrow=borrow)
        # When storing data on the GPU it has to be stored as floats
        # therefore we will store the labels as ``floatX`` as well
        # (``shared_y`` does exactly that). But during our computations
        # we need them as ints (we use labels as index, and if they are
        # floats it doesn't make sense) therefore instead of returning
        # ``shared_y`` we will have to cast it to int. This little hack
        # lets ous get around this issue

        return T.cast(shared_x, 'int32'), T.cast(shared_y, 'int32'),T.cast(shared_z, 'int32')

def iterate_minibatches(inputs,inputs2, targets, batch_size, shuffle=False):
    ''' Taken from the mnist.py example of Lasagne'''

    targets = np.asarray(targets)
    assert inputs.shape[0] == targets.size
    if shuffle:
        indices = np.arange(inputs.shape[0])
        np.random.shuffle(indices)
    for start_idx in range(0, inputs.shape[0] - batch_size + 1, batch_size):
        if shuffle:
            excerpt = indices[start_idx:start_idx + batch_size]
        else:
            excerpt = slice(start_idx, start_idx + batch_size)
        yield inputs[excerpt], inputs2[excerpt], targets[excerpt]

def read_model_data(model, filename):
    """Unpickles and loads parameters into a Lasagne model."""
    filename = os.path.join('./', '%s.%s' % (filename, 'params'))
    with open(filename, 'r') as f:
        data = pickle.load(f)
    lasagne.layers.set_all_param_values(model, data)


def write_model_data(model, filename):
    """Pickels the parameters within a Lasagne model."""
    data = lasagne.layers.get_all_param_values(model)
    filename = os.path.join('./', filename)
    filename = '%s.%s' % (filename, 'params')
    with open(filename, 'w+') as f:
        pickle.dump(data, f)


