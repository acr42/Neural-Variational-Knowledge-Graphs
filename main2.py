# -*- coding: utf-8 -*-

import tensorflow as tf
import vkge

#
import logging

logger = logging.getLogger(__name__)

flags = tf.app.flags
flags.DEFINE_float("learning_rate", 0.1, "Learning rate of adam optimizer [0.1]")
flags.DEFINE_float("init_sig", 6.0, "Initalised variance of variables [6.0]")
flags.DEFINE_float("init_sig2", 6.0, "Initalised variance of variables [6.0]")
flags.DEFINE_float("mog_split", 0.5, "Split between spike and slab [6.0]")
flags.DEFINE_integer("embedding_size", 50, "The dimension of graph embeddings [50]")
flags.DEFINE_integer("batch_size", 14145, "Batch Size [14145]")
flags.DEFINE_boolean("alt_cost", True, "Switch for compression cost to be used in training [True]")
flags.DEFINE_boolean("static_mean", False,
                     "Switch as to if mean is fixed at 0 or can train with random normal init [False]")
flags.DEFINE_boolean("alternating_updates", False, "Alternate updates around each distribution[False]")
flags.DEFINE_boolean("Sigma_alt", True, "Alternate between two different standard dev calculations [True]")
flags.DEFINE_boolean("projection", True, "Alternate between using a projection on the means [False]")
flags.DEFINE_boolean("tensorboard", True, "Define for tensorboard statistics to be saved [False]")
flags.DEFINE_boolean("static_pred", False, "Defines if predicate embeddings are variational or fixed point [False]")
flags.DEFINE_boolean("decay_kl", False, "Defines if KL inverse decays [False]")
flags.DEFINE_float("margin", 5, "Choose optimiser loss, select the margin for hinge loss [5]")
flags.DEFINE_string("file_name", '~/', "file name for tensorboard file ['--']")
FLAGS = flags.FLAGS


def main(_):
    logger.warn("creating model with flags \t {}".format(flags.FLAGS.__flags))

    vkge.VKGE2(embedding_size=FLAGS.embedding_size, lr=FLAGS.learning_rate,init_sig=FLAGS.init_sig, alt_cost=FLAGS.alt_cost, batch_s=FLAGS.batch_size,
              static_mean=FLAGS.static_mean, alt_updates=FLAGS.alternating_updates, sigma_alt=FLAGS.Sigma_alt,
               margin=FLAGS.margin, file_name=FLAGS.file_name, tensorboard=FLAGS.tensorboard
              , projection=FLAGS.projection, static_pred=FLAGS.static_pred, decay_kl=FLAGS.decay_kl)


if __name__ == '__main__':
    tf.app.run()