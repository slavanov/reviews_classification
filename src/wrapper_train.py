from __future__ import print_function
import pandas as pd
import logging
from train import TrainModel


class WrapperTrainModel:
    """
    this class run different configurations.
    input:
        1. configuration properties to check
    output:
        1. hyper-parameters tuning using grid search
        2. call to inner class (train) to check every configuration
    """

    def __init__(self, input_data_file, vertical_type, output_results_folder, tensor_board_dir, lstm_parameters_dict,
                 df_configuration_dict, cv_configuration, test_size, embedding_pre_trained,
                 multi_class_configuration_dict, attention_configuration_dict, embedding_type):

        # file arguments
        self.input_data_file = input_data_file              # csv input file
        self.vertical_type = vertical_type                  # 'fashion'/'motors'
        self.output_results_folder = output_results_folder  # output folder to store results
        self.tensor_board_dir = tensor_board_dir

        self.test_size = test_size  # 0.2
        self.embedding_pre_trained = embedding_pre_trained
        self.lstm_parameters_dict = lstm_parameters_dict
        self.df_configuration_dict = df_configuration_dict  # df configuration - how to manipulate data pre-processing
        self.cv_configuration = cv_configuration        # Cross validation configuration
        self.verbose_flag = True

        self.multi_class_configuration_dict = multi_class_configuration_dict
        self.attention_configuration_dict = attention_configuration_dict
        self.embedding_type = embedding_type

        from time import gmtime, strftime
        self.cur_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

        # define data frame needed for analyzing data
        self.df = pd.DataFrame()
        self.train_df = pd.DataFrame()
        self.test_df = pd.DataFrame()

    # init log file
    def init_debug_log(self):
        import logging

        lod_dir = './log/wrapper_train/'

        log_file_name = '{}_vertical={}_group={}_optimizer={}.log'.format(
                            str(self.cur_time),
                            str(self.vertical_type),
                            str(self.df_configuration_dict['y_positive_name']),
                            str(self.lstm_parameters_dict['optimizer'])
                        )
        import os
        if not os.path.exists(lod_dir):
            os.makedirs(lod_dir)

        logging.basicConfig(filename=lod_dir + log_file_name,
                            format='%(asctime)s, %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)

        # print result in addition to log file
        if self.verbose_flag:
            stderrLogger = logging.StreamHandler()
            stderrLogger.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
            logging.getLogger().addHandler(stderrLogger)

        logging.info("")
        return

    def check_input(self):

        # glove embedding size must be one of '50', '100', '200', '300'
        '''if self.embedding_pre_trained and self.embedding_type == 'glove':
            for e_s in self.lstm_parameters_dict['embedding_size']:
                if e_s not in [50, 100, 200, 300]:
                    raise('glove embedding size must be one of [50, 100, 200, 300]')'''

        if 'type' not in embedding_type or 'path' not in embedding_type:
            raise ValueError('embedding type must contain path and type key')

        if self.lstm_parameters_dict['optimizer'] not in ['adam', 'rmsprop']:
            raise ValueError('unknown optimizer')

        if self.multi_class_configuration_dict['multi_class_bool'] and self.attention_configuration_dict['use_attention_bool']:
            raise ValueError('currently attention model is only support for single class classification')

        if not self.cv_configuration['use_cv_bool']:
            raise ValueError('CV bool must be true')

        if len(self.multi_class_configuration_dict['multi_class_label']) != len(self.multi_class_configuration_dict['loss_weights']):
            raise ValueError('MTL class numbers miss-match')


    # iterate over all configuration, build model for each
    def run_wrapper_model(self):

        total_iteration = len(self.lstm_parameters_dict['maxlen'])\
                          * len(self.lstm_parameters_dict['batch_size'])\
                          * len(self.lstm_parameters_dict['lstm_hidden_layer'])\
                          * len(self.lstm_parameters_dict['dropout'])

        model_num = 1
        for maxlen in self.lstm_parameters_dict['maxlen']:
            for batch_size in self.lstm_parameters_dict['batch_size']:
                for dropout in self.lstm_parameters_dict['dropout']:
                    for lstm_hidden_layer in self.lstm_parameters_dict['lstm_hidden_layer']:

                        # run single lstm model with the following configuration
                        try:
                            lstm_parameters_dict = {
                                'max_features': self.lstm_parameters_dict['max_features'],
                                'maxlen': maxlen,
                                'batch_size': batch_size,
                                'embedding_size': self.lstm_parameters_dict['embedding_size'],
                                'lstm_hidden_layer': lstm_hidden_layer,    # TODO change to different values
                                'num_epoch': self.lstm_parameters_dict['num_epoch'],
                                'dropout': dropout,  # 0.2
                                'recurrent_dropout': self.lstm_parameters_dict['recurrent_dropout'],
                                'tensor_board_bool': self.lstm_parameters_dict['tensor_board_bool'],
                                'max_num_words': self.lstm_parameters_dict['max_num_words'],
                                'optimizer': self.lstm_parameters_dict['optimizer'],
                                'patience': self.lstm_parameters_dict['patience']
                            }

                            logging.info('')
                            logging.info('**************************************************************')
                            logging.info('')
                            logging.info('start model number: ' + str(model_num) + '/' + str(total_iteration))
                            logging.info('lstm parameters: ' + str(lstm_parameters_dict))

                            train_obj = TrainModel(self.input_data_file,
                                                   self.vertical_type,
                                                   self.output_results_folder,
                                                   self.tensor_board_dir,
                                                   lstm_parameters_dict,
                                                   df_configuration_dict,
                                                   multi_class_configuration_dict,
                                                   attention_configuration_dict,
                                                   self.cv_configuration,
                                                   self.test_size,
                                                   self.embedding_pre_trained,
                                                   self.embedding_type,
                                                   logging)

                            model_num += 1

                            logging.info('')
                            train_obj.load_clean_csv_results()  # load data set
                            train_obj.df_pre_processing()
                            train_obj.run_experiment()
                        except Exception as e:

                            logging.info(
                                'exception found during maxlen: {}, batch_size: {}, dropout: {}, lstm_hidden_layer: {}'
                                    .format(maxlen, batch_size, dropout, lstm_hidden_layer)
                            )
                            logging.info('trace: {}'.format(e))
                            logging.info('continue next configuration')
                            logging.info('')
                            logging.info('')
                            logging.info('')

        return


def main(input_data_file, vertical_type, output_results_folder, tensor_board_dir, lstm_parameters_dict,
         df_configuration_dict, cv_configuration, test_size, embedding_pre_trained, multi_class_configuration_dict,
         attention_configuration_dict, embedding_type):

    train_obj = WrapperTrainModel(input_data_file, vertical_type, output_results_folder, tensor_board_dir,
                           lstm_parameters_dict, df_configuration_dict, cv_configuration,
                           test_size, embedding_pre_trained, multi_class_configuration_dict,
                                  attention_configuration_dict,embedding_type)

    train_obj.init_debug_log()              # init log file
    train_obj.check_input()
    train_obj.run_wrapper_model()        # call to LSTM model class


if __name__ == '__main__':

    # input file name
    vertical_type = 'fashion'  # 'fashion'/'motors'
    output_results_folder = '../results/'
    tensor_board_dir = '../results/tensor_board_graph/'
    test_size = 0.2
    embedding_pre_trained = True
    embedding_type = {
        'type': 'gensim',   # 'glove', 'gensim'
        # 'path': '../data/word2vec_pretrained/motors/d_300_k_712904_w_6_e_60_v_motors'       # path to gensim wv
        # 'path': '../data/word2vec_pretrained/motors/d_100_k_712904_w_10_e_60_v_motors',
        'path': '../data/word2vec_pretrained/fashion/d_100_k_1341062_w_10_e_60_v_fashion',
        'd': 100,
        'w': 10,
        'e': 60
        # 'path_dor': '../data/word2vec_amazon_pretrained/model.bin'
    }
    # fashion wv path = '../data/word2vec_pretrained/fashion/d_300_k_1341062_w_6_e_70_v_fashion'

    cv_configuration = {
        'use_cv_bool': True,
        'num_fold': 5
    }

    # possible columns names:
    # 'subjective_sentence'	'missing_context' 'Refers to a specific listing aspect'
    # 'Non-informative sentence' 'failure_reason'

    multi_class_configuration_dict = {
        'multi_class_bool': False,                                   # whether to do single/multi class classification
        'multi_class_label': [
            'review_tag', 'missing_context', 'Non-informative sentence', 'Refers to a specific listing aspect'
        ],
        # 'Non-informative sentence', 'Refers to a specific listing aspect', , 'subjective_sentence', 'missing_context'],      # ['review_tag', 'missing_context'] ['review_tag', 'subjective_sentence']
        # 'multi_class_label': ['subjective_sentence', 'review_tag', 'missing_context'],
        'loss_weights': [4, 1, 2, 2]
    }

    attention_configuration_dict = {
        'use_attention_bool': True
    }

    # tag bad/good prediction
    df_configuration_dict = {
        'x_column': 'Review',
        'y_column': 'review_tag',  # 'failure_reason'\'review_tag',
        'y_positive': 1,
        'y_positive_name': 'Good'  # positive group, will add to folder results name
    }

    # quick hyper-parameters tuning

    lstm_parameters_dict = {
        'max_features': 200000,
        'maxlen': [20],                 # 20      # [8, 10, 15, 20],
        'batch_size': [32],            # 32
        'embedding_size': 100,          # fit to word2vec version dimension
        'lstm_hidden_layer': [250, 325, 450, 200],  # [50, 125, 175, 225, 300],  # TODO change  # 50, 100,
        'num_epoch': 30,
        'dropout': [0.23, 0.33, 0.28],  # 0.28, 0.23,  [0.33, 0.28, 0.23], # , 0.38],  # 0.2, 0.35, 0.5
        'recurrent_dropout': 0.1,       # TODO currently does not use in the model
        'optimizer': 'rmsprop',         # 'rmsprop'/'adam'
        'patience': 3,
        'tensor_board_bool': True,
        'max_num_words': None           # number of words allow in the tokenizer process - keras text tokenizer
    }

    # quick hyper-parameters tuning
    """
    lstm_parameters_dict = {
        'max_features': 200000,
        'maxlen': [10],  # 20      # [8, 10, 15, 20],
        'batch_size': [128],  # 32
        'embedding_size': 100,  # fit to word2vec version dimension
        'lstm_hidden_layer': [150],     # [50, 125, 175, 225, 300],  # TODO change  # 50, 100,
        'num_epoch': 10,
        'dropout': [0.38, 0.33, 0.23],    # [0.33, 0.28, 0.23], # , 0.38],  # 0.2, 0.35, 0.5
        'recurrent_dropout': 0.1,  # TODO currently does not use in the model
        'optimizer': 'rmsprop',    # 'rmsprop' 'adam'
        'patience': 1,
        'tensor_board_bool': True,
        'max_num_words': None  # number of words allow in the tokenizer process - keras text tokenizer
    }
    """

    if vertical_type == 'fashion':
        input_data_file = '../data/clean/clean_data_fashion.csv'
        input_data_file = '../data/clean/clean_data_multi_fashion.csv'
        input_data_file = '../data/clean/clean_data_multi_new_fashion.csv'
        # input_data_file = '../data/clean/clean_data_multi_balanced.csv'

    elif vertical_type == 'motors':
        input_data_file = '../data/clean/clean_data_motors.csv'
        input_data_file = '../data/clean/clean_data_multi_new_motors.csv'
        # input_data_file = '../data/clean/clean_data_motors_multi_balanced.csv'

    else:
        raise()

    main(input_data_file, vertical_type, output_results_folder, tensor_board_dir, lstm_parameters_dict,
         df_configuration_dict, cv_configuration, test_size, embedding_pre_trained, multi_class_configuration_dict,
         attention_configuration_dict, embedding_type)
