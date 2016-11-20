from rl.agent.double_dqn import DoubleDQN
from rl.policy import TargetedEpsilonGreedyPolicy
from rl.util import logger
from keras.models import Sequential
from keras.layers.core import Dense
from keras.optimizers import SGD


class LunarDoubleDQN(DoubleDQN):

    def __init__(self, *args, **kwargs):
        super(LunarDoubleDQN, self).__init__(*args, **kwargs)
        # change the policy
        self.policy = TargetedEpsilonGreedyPolicy(self)

    def build_model(self):
        model = Sequential()
        model.add(Dense(100,
                        input_shape=(self.env_spec['state_dim'],),
                        init='lecun_uniform', activation='sigmoid'))
        model.add(Dense(self.env_spec['action_dim'], init='lecun_uniform'))
        logger.info("Model 1 summary")
        model.summary()
        self.model = model

        model2 = Sequential.from_config(model.get_config())
        logger.info("Model 2 summary")
        model2.summary()
        self.model2 = model2

        self.optimizer = SGD(lr=self.learning_rate, momentum=0.1)
        self.model.compile(
            loss='mean_squared_error', optimizer=self.optimizer)
        self.model2.compile(
            loss='mean_squared_error', optimizer=self.optimizer)
        logger.info("Models built and compiled")

        return self.model, self.model2