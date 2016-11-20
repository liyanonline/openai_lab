import numpy as np
from rl.agent.base_agent import Agent
from rl.policy import EpsilonGreedyPolicy
from rl.util import logger, pp
from keras.models import Sequential
from keras.layers.core import Dense
from keras.optimizers import SGD
# from keras.regularizers import l1, l2
# from keras.constraints import maxnorm
# from keras.objectives import mse


class DQN(Agent):

    '''
    The base class of DQNs, with the core methods
    The simplest deep Q network,
    with epsilon-greedy method and
    Bellman equation for value, using neural net.
    '''

    def __init__(self, env_spec,
                 gamma=0.95, learning_rate=0.1,
                 init_e=1.0, final_e=0.1, e_anneal_episodes=1000,
                 batch_size=16, n_epoch=1):
        super(DQN, self).__init__(env_spec)
        self.policy = EpsilonGreedyPolicy(self)

        self.gamma = gamma
        self.learning_rate = learning_rate
        self.init_e = init_e
        self.final_e = final_e
        self.e = self.init_e
        self.e_anneal_episodes = e_anneal_episodes
        self.batch_size = batch_size
        self.n_epoch = n_epoch
        logger.info(pp.pformat(self.env_spec))
        self.build_model()

    def build_model(self):
        model = Sequential()
        # Not clear how much better the algorithm is with regularization
        model.add(Dense(4,
                        input_shape=(self.env_spec['state_dim'],),
                        init='lecun_uniform', activation='sigmoid'))
        model.add(Dense(self.env_spec['action_dim'], init='lecun_uniform'))
        model.summary()
        self.model = model

        self.optimizer = SGD(lr=self.learning_rate)
        self.model.compile(loss='mean_squared_error', optimizer=self.optimizer)
        logger.info("Model built and compiled")
        return self.model

    def update_n_epoch(self, sys_vars):
        '''
        Increase epochs at the beginning of each session,
        for training for later episodes,
        once it has more experience
        Best so far, increment num epochs every 2 up to a max of 5
        '''
        if (self.n_epoch < 5 and
                sys_vars['t'] == 0 and
                sys_vars['epi'] % 2 == 0):
            self.n_epoch += 1
        return self.n_epoch

    def select_action(self, state):
        '''epsilon-greedy method'''
        return self.policy.select_action(state)

    def train(self, sys_vars, replay_memory):
        '''
        step 1,2,3,4 of algo.
        replay_memory is provided externally
        '''
        self.policy.update(sys_vars, replay_memory)
        self.update_n_epoch(sys_vars)

        loss_total = 0
        for epoch in range(self.n_epoch):
            minibatch = replay_memory.rand_minibatch(self.batch_size)
            # note the computed values below are batched in array
            Q_states = self.model.predict(minibatch['states'])
            Q_next_states = self.model.predict(minibatch['next_states'])
            Q_next_states_max = np.amax(Q_next_states, axis=1)
            # make future reward 0 if exp is terminal
            Q_targets_a = minibatch['rewards'] + self.gamma * \
                (1 - minibatch['terminals']) * Q_next_states_max
            # set batch Q_targets of a as above, the rest as is
            # minibatch['actions'] is one-hot encoded
            Q_targets = minibatch['actions'] * Q_targets_a[:, np.newaxis] + \
                (1 - minibatch['actions']) * Q_states

            # logger.info("minibatch actions: {}\n Q_targets_a (reshapes): {}"
            #             "\n Q_states: {}\n Q_targets: {}\n\n".format(
            #                 minibatch['actions'], Q_targets_a[
            #                     :, np.newaxis], Q_states,
            #                 Q_targets))

            loss = self.model.train_on_batch(minibatch['states'], Q_targets)
            loss_total += loss
        avg_loss = loss_total / self.n_epoch
        sys_vars['loss'].append(avg_loss)
        return avg_loss

    def save(self, model_path, global_step=None):
        logger.info('Saving model checkpoint')
        self.model.save_weights(model_path)

    def restore(self, model_path):
        self.model.load_weights(model_path, by_name=False)