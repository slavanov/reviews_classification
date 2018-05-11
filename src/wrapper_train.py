from __future__ import print_function
import pandas as pd
import logging
from train import TrainModel


class WrapperTrainModel:
    '''
    this class run different configurations.
    input:
        1. configuration properties to check
    output:
        1. hyper-parameters tuning using grid search
        2. call to inner class (train) to check every configuration
    '''

    def __init__(self, input_data_file, vertical_type, output_results_folder, tensor_board_dir, lstm_parameters_dict,
                 df_configuration_dict, cv_configuration, test_size, embedding_pre_trained,
                 multi_class_configuration_dict, attention_configuration_dict):

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

        from time import gmtime, strftime
        self.cur_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

        # define data frame needed for analyzing data
        self.df = pd.DataFrame()
        self.train_df = pd.DataFrame()
        self.test_df = pd.DataFrame()

    # init log file
    def init_debug_log(self):
        import logging

        lod_dir = '/Users/sguyelad/PycharmProjects/reviews_classifier/log/wrapper_train/'

        log_file_name = str(self.cur_time) + \
                        '_vertical=' + str(self.vertical_type) + \
                        '_group=' + str(self.df_configuration_dict['y_positive_name']) + \
                        '_optimizer=' + str(self.lstm_parameters_dict['optimizer']) + '.log'
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
        if self.embedding_pre_trained:
            for e_s in self.lstm_parameters_dict['embedding_size']:
                if e_s not in [50, 100, 200, 300]:
                    raise('glove embedding size must be one of [50, 100, 200, 300]')

        if self.lstm_parameters_dict['optimizer'] not in ['adam', 'rmsprop']:
            raise('unknown optimizer')

        if self.multi_class_configuration_dict['multi_class_bool'] and self.attention_configuration_dict['use_attention_bool']:
            raise('currently attention model is only support for single class classification')

        return

    # iterate over all configuration, build model for each
    def run_wrapper_model(self):

        total_iteration = len(self.lstm_parameters_dict['maxlen'])\
                          * len(self.lstm_parameters_dict['batch_size'])\
                          * len(self.lstm_parameters_dict['embedding_size'])\
                          * len(self.lstm_parameters_dict['dropout'])

        model_num = 1
        for maxlen in self.lstm_parameters_dict['maxlen']:
            for batch_size in self.lstm_parameters_dict['batch_size']:
                for dropout in self.lstm_parameters_dict['dropout']:
                    for embedding_size in self.lstm_parameters_dict['embedding_size']:

                        # run single lstm model with the following configuration

                        lstm_parameters_dict = {
                            'max_features': self.lstm_parameters_dict['max_features'],
                            'maxlen': maxlen,
                            'batch_size': batch_size,
                            'embedding_size': embedding_size,
                            'lstm_hidden_layer': embedding_size,    # TODO change to different values
                            'num_epoch': self.lstm_parameters_dict['num_epoch'],
                            'dropout': dropout,  # 0.2
                            'recurrent_dropout': dropout,  # 0.2
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
                                               logging)

                        model_num += 1

                        logging.info('')
                        train_obj.load_clean_csv_results()  # load data set
                        train_obj.df_pre_processing()
                        train_obj.run_experiment()

        return


def main(input_data_file, vertical_type, output_results_folder, tensor_board_dir, lstm_parameters_dict,
         df_configuration_dict, cv_configuration, test_size, embedding_pre_trained, multi_class_configuration_dict,
         attention_configuration_dict):

    train_obj = WrapperTrainModel(input_data_file, vertical_type, output_results_folder, tensor_board_dir,
                           lstm_parameters_dict, df_configuration_dict, cv_configuration,
                           test_size, embedding_pre_trained, multi_class_configuration_dict,
                                  attention_configuration_dict)

    train_obj.init_debug_log()              # init log file
    train_obj.check_input()
    train_obj.run_wrapper_model()        # call to LSTM model class


if __name__ == '__main__':

    # input file name
    vertical_type = 'fashion'       # 'fashion'/'motors'
    output_results_folder = '../results/'
    tensor_board_dir = '../results/tensor_board_graph/'
    test_size = 0.2
    embedding_pre_trained = True

    cv_configuration = {
        'use_cv_bool': True,
        'num_fold': 5
    }

    multi_class_configuration_dict = {
        'multi_class_bool': True,      # whether to do single/multi class classification
        'multi_class_label': ['review_tag',
                              'subjective_sentence']
                              # 'missing_context']
    }

    attention_configuration_dict = {
        'use_attention_bool': False,
        # 'attention_before_lstm_bool': False,
        # 'single_attention_vector': False,
        'attention_with_context': True
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
        'maxlen': [5, 20, 25],  # 20      # [8, 10, 15, 20],
        'batch_size': [128, 32],  # 32
        'embedding_size': [50, 300, 200],  # 50, 100, 200, 300   [64, 128, 256],
        'lstm_hidden_layer': [200],  # 50, 100,
        'num_epoch': 30,
        'dropout': [0.28, 0.38],  # 0.2, 0.35, 0.5
        'recurrent_dropout': [0.35],  # 0.2, 0.35, 0.5
        'optimizer': 'rmsprop',    # 'rmsprop'
        'patience': 5,
        'tensor_board_bool': True,
        'max_num_words': None  # number of words allow in the tokenizer process - keras text tokenizer
    }

    if vertical_type == 'fashion':
        input_data_file = '../data/clean/clean_data_fashion.csv'
        input_data_file = '../data/clean/clean_data_multi_fashion.csv'
    elif vertical_type == 'motors':
        input_data_file = '../data/clean/clean_data_motors.csv'
    else:
        raise()

    main(input_data_file, vertical_type, output_results_folder, tensor_board_dir, lstm_parameters_dict,
         df_configuration_dict, cv_configuration, test_size, embedding_pre_trained, multi_class_configuration_dict,
         attention_configuration_dict)