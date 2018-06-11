
# -*- coding: utf-8 -*-

import math
import numpy as np
import tensorflow as tf
import vkge

from vkge.knowledgebase import Fact, KnowledgeBaseParser

import vkge.models as models
from vkge.training import constraints, corrupt, index
from vkge.training.util import make_batches
import vkge.io as io


# new
#
import logging
logger = logging.getLogger(__name__)

#
# class VKGE:
#     def __init__(self, embedding_size=5,batch_s=14145, lr=0.001, b1=0.9, b2=0.999, eps=1e-08, GPUMode=False, ent_sig=6.0,
#                  alt_cost=True,train_mean=False,alt_updates=False):
#         super().__init__()
#
#         ent_sigma = np.log(ent_sig**2)
#         pred_sigma = ent_sigma #adjust for correct format for model input
#         predicate_embedding_size = embedding_size
#         entity_embedding_size = embedding_size
#
#         triples = io.read_triples("data/wn18/wordnet-mlj12-train.txt")  # choose dataset
#         test_triples = io.read_triples("data/wn18/wordnet-mlj12-test.txt")
#
#         self.random_state = np.random.RandomState(0)
#         self.GPUMode = GPUMode
#         self.alt_cost = alt_cost
#         self.nb_examples = len(triples)
#         self.static_mean=train_mean
#         self.alt_updates=alt_updates
#
#
#         logger.warn('Parsing the facts in the Knowledge Base ..')
#
#         # logger.warn('Parsing the facts in the Knowledge Base ..')
#         self.facts = [Fact(predicate_name=p, argument_names=[s, o]) for s, p, o in triples]
#
#         self.test_facts = [Fact(predicate_name=p, argument_names=[s, o]) for s, p, o in test_triples]
#
#         self.test_parser = KnowledgeBaseParser(self.test_facts)
#         self.parser = KnowledgeBaseParser(self.facts)
#
#         ##### for test time ######
#         all_triples = triples + test_triples
#         entity_set = {s for (s, p, o) in all_triples} | {o for (s, p, o) in all_triples}
#         predicate_set = {p for (s, p, o) in all_triples}
#         self.entity_to_idx = {entity: idx for idx, entity in enumerate(sorted(entity_set))}
#         self.predicate_to_idx = {predicate: idx for idx, predicate in enumerate(sorted(predicate_set))}
#         self.nb_entities, self.nb_predicates = len(entity_set), len(predicate_set)
#         ############################
#
#         optimizer = tf.train.AdamOptimizer(learning_rate=lr, beta1=b1, beta2=b2, epsilon=eps)
#         self.build_model(self.nb_entities, entity_embedding_size, self.nb_predicates, predicate_embedding_size,
#                          optimizer,
#                          ent_sigma, pred_sigma)
#
#         self.train(nb_epochs=1000, test_triples=test_triples, all_triples=all_triples,batch_size=batch_s)
#
#     @staticmethod
#     def input_parameters(inputs, parameters_layer):
#         parameters = tf.nn.embedding_lookup(parameters_layer, inputs)
#         mu, log_sigma_square = tf.split(value=parameters, num_or_size_splits=2, axis=1)
#         return mu, log_sigma_square
#
#     @staticmethod
#     def sample_embedding(mu, log_sigma_square):
#         sigma = tf.sqrt(tf.exp(log_sigma_square))
#         embedding_size = mu.get_shape()[1].value
#         eps = tf.random_normal((1, embedding_size), 0, 1, dtype=tf.float32)
#         return mu + sigma * eps
#
#     def build_model(self, nb_entities, entity_embedding_size, nb_predicates, predicate_embedding_size, optimizer,
#                     ent_sig, pred_sig):
#         self.s_inputs = tf.placeholder(tf.int32, shape=[None])
#         self.p_inputs = tf.placeholder(tf.int32, shape=[None])
#         self.o_inputs = tf.placeholder(tf.int32, shape=[None])
#         self.y_inputs = tf.placeholder(tf.bool, shape=[None])
#
#         self.build_encoder(nb_entities, entity_embedding_size, nb_predicates, predicate_embedding_size, ent_sig,
#                            pred_sig)
#         self.build_decoder()
#
#         self.KL_discount = tf.placeholder(tf.float32)  # starts at 0.5
#
#         # Kullback Leibler divergence
#         self.e_objective = 0.0
#
#         self.e_objective -= 0.5 * tf.reduce_sum(
#             1. + self.log_sigma_sq_s - tf.square(self.mu_s) - tf.exp(self.log_sigma_sq_s))
#         self.e_objective -= 0.5 * tf.reduce_sum(
#             1. + self.log_sigma_sq_p - tf.square(self.mu_p) - tf.exp(self.log_sigma_sq_p))
#         self.e_objective -= 0.5 * tf.reduce_sum(
#             1. + self.log_sigma_sq_o - tf.square(self.mu_o) - tf.exp(self.log_sigma_sq_o))
#
#         self.e_objective = (self.e_objective * self.KL_discount)
#         # Log likelihood
#         self.g_objective = -tf.reduce_sum(
#             tf.log(tf.where(condition=self.y_inputs, x=self.p_x_i, y=1 - self.p_x_i) + 1e-4))
#
#         self.elbo = self.g_objective + self.e_objective
#
#         self.training_step = optimizer.minimize(self.elbo)
#
#     def build_encoder(self, nb_entities, entity_embedding_size, nb_predicates, predicate_embedding_size, ent_sig,
#                       pred_sig):
#         logger.warn('Building Inference Networks q(h_x | x) ..')
#
#         # logger.warn('Building Inference Networks q(h_x | x) ..')
#
#         with tf.variable_scope("encoder"):
#
#             if self.static_mean:
#
#                 self.entity_embedding_mean = tf.get_variable('entities_mean',
#                                                          shape=[nb_entities + 1, entity_embedding_size],
#                                                          initializer=tf.zeros_initializer(), dtype=tf.float32,trainable=False)
#             else:
#
#                 self.entity_embedding_mean = tf.get_variable('entities_mean',
#                                                              shape=[nb_entities + 1, entity_embedding_size],
#                                                              initializer=tf.initializers.random_normal(), dtype=tf.float32,trainable=True)
#
#             self.entity_embedding_sigm = tf.get_variable('entities_sigma',
#                                                          shape=[nb_entities + 1, entity_embedding_size],
#                                                          initializer=tf.ones_initializer(), dtype=tf.float32)
#
#             self.entity_embedding_sigma = tf.Variable(self.entity_embedding_sigm.initialized_value() * ent_sig,
#                                                       dtype=tf.float32)
#
#             self.mu_s = tf.nn.embedding_lookup(self.entity_embedding_mean, self.s_inputs)
#             self.log_sigma_sq_s = tf.nn.embedding_lookup(self.entity_embedding_sigma, self.s_inputs)
#             self.h_s = VKGE.sample_embedding(self.mu_s, self.log_sigma_sq_s)
#
#             self.mu_o = tf.nn.embedding_lookup(self.entity_embedding_mean, self.o_inputs)
#             self.log_sigma_sq_o = tf.nn.embedding_lookup(self.entity_embedding_sigma, self.o_inputs)
#             self.h_o = VKGE.sample_embedding(self.mu_o, self.log_sigma_sq_o)
#
#             self.predicate_embedding_mean = tf.get_variable('predicate_mean',
#                                                             shape=[nb_predicates + 1, predicate_embedding_size],
#                                                             initializer=tf.zeros_initializer(), dtype=tf.float32,trainable=False)
#             self.predicate_embedding_sigm = tf.get_variable('predicate_sigma',
#                                                             shape=[nb_predicates + 1, predicate_embedding_size],
#                                                             initializer=tf.ones_initializer(), dtype=tf.float32)
#
#             self.predicate_embedding_sigma = tf.Variable(self.predicate_embedding_sigm.initialized_value() * pred_sig,
#                                                          dtype=tf.float32)
#
#             self.mu_p = tf.nn.embedding_lookup(self.predicate_embedding_mean, self.p_inputs)
#             self.log_sigma_sq_p = tf.nn.embedding_lookup(self.predicate_embedding_sigma, self.p_inputs)
#             self.h_p = VKGE.sample_embedding(self.mu_p, self.log_sigma_sq_p)
#
#     def build_decoder(self):
#
#         logger.warn('Building Inference Network p(y|h) ..')
#
#         with tf.variable_scope('decoder'):
#             model = models.BilinearDiagonalModel(subject_embeddings=self.h_s, predicate_embeddings=self.h_p,
#                                                  object_embeddings=self.h_o)
#             self.scores = model()
#             self.p_x_i = tf.sigmoid(self.scores)
#
#     def train(self, test_triples, all_triples, batch_size, session=0, nb_epochs=1000):
#         index_gen = index.GlorotIndexGenerator()
#         neg_idxs = np.array(sorted(set(self.parser.entity_to_index.values())))
#
#         subj_corruptor = corrupt.SimpleCorruptor(index_generator=index_gen, candidate_indices=neg_idxs,
#                                                  corr_obj=False)
#         obj_corruptor = corrupt.SimpleCorruptor(index_generator=index_gen, candidate_indices=neg_idxs,
#                                                 corr_obj=True)
#
#         train_sequences = self.parser.facts_to_sequences(self.facts)
#
#         Xs = np.array([s_idx for (_, [s_idx, _]) in train_sequences])
#         Xp = np.array([p_idx for (p_idx, _) in train_sequences])
#         Xo = np.array([o_idx for (_, [_, o_idx]) in train_sequences])
#
#         assert Xs.shape == Xp.shape == Xo.shape
#
#         nb_samples = Xs.shape[0]
#         # batch_size = math.ceil(nb_samples / nb_batches)
#         nb_batches= math.ceil(nb_samples / batch_size)
#         # logger.warn("Samples: {}, no. batches: {} -> batch size: {}".format(nb_samples, nb_batches, batch_size))
#         logger.warn("Samples: {}, no. batches: {} -> batch size: {}".format(nb_samples, nb_batches, batch_size))
#
#         # projection_steps = [constraints.unit_cube(self.entity_parameters_layer) if unit_cube
#         #                     else constraints.unit_sphere(self.entity_parameters_layer, norm=1.0)]
#         minloss = 10000
#
#         minepoch = 0
#
#         ####### COMPRESSION COST PARAMETERS
#
#         M = int(np.ceil((self.nb_examples * nb_epochs / batch_size)) + 1)
#
#         pi_s = np.log(2.0)*M
#         pi_e = np.log(2.0)
#
#         pi = np.exp(np.linspace(pi_s, pi_e, M)-M*np.log(2.0))
#
#         counter = 0
#
#         #####################
#
#         init_op = tf.global_variables_initializer()
#         with tf.Session() as session:
#             session.run(init_op)
#             for epoch in range(1, nb_epochs + 1):
#                 order = self.random_state.permutation(nb_samples)
#                 Xs_shuf, Xp_shuf, Xo_shuf = Xs[order], Xp[order], Xo[order]
#
#                 Xs_sc, Xp_sc, Xo_sc = subj_corruptor(Xs_shuf, Xp_shuf, Xo_shuf)
#                 Xs_oc, Xp_oc, Xo_oc = obj_corruptor(Xs_shuf, Xp_shuf, Xo_shuf)
#
#                 batches = make_batches(nb_samples, batch_size)
#
#                 loss_values = []
#                 total_loss_value = 0
#
#                 nb_versions = 3
#
#                 for batch_start, batch_end in batches:
#                     curr_batch_size = batch_end - batch_start
#
#                     Xs_batch = np.zeros((curr_batch_size * nb_versions), dtype=Xs_shuf.dtype)
#                     Xp_batch = np.zeros((curr_batch_size * nb_versions), dtype=Xp_shuf.dtype)
#                     Xo_batch = np.zeros((curr_batch_size * nb_versions), dtype=Xo_shuf.dtype)
#
#                     # Positive Example
#                     Xs_batch[0::nb_versions] = Xs_shuf[batch_start:batch_end]
#                     Xp_batch[0::nb_versions] = Xp_shuf[batch_start:batch_end]
#                     Xo_batch[0::nb_versions] = Xo_shuf[batch_start:batch_end]
#
#                     # Negative examples (corrupting subject)
#                     Xs_batch[1::nb_versions] = Xs_sc[batch_start:batch_end]
#                     Xp_batch[1::nb_versions] = Xp_sc[batch_start:batch_end]
#                     Xo_batch[1::nb_versions] = Xo_sc[batch_start:batch_end]
#
#                     # Negative examples (corrupting object)
#                     Xs_batch[2::nb_versions] = Xs_oc[batch_start:batch_end]
#                     Xp_batch[2::nb_versions] = Xp_oc[batch_start:batch_end]
#                     Xo_batch[2::nb_versions] = Xo_oc[batch_start:batch_end]
#
#                     y = np.zeros_like(Xp_batch)
#                     y[0::nb_versions] = 1
#
#                     if self.alt_cost:  # if compression cost
#
#                         loss_args = {
#                             self.KL_discount: pi[counter],
#                             self.s_inputs: Xs_batch,
#                             self.p_inputs: Xp_batch,
#                             self.o_inputs: Xo_batch,
#                             self.y_inputs: y
#                         }
#
#                     else:
#
#                         loss_args = {
#                             self.KL_discount: 1.0,
#                             self.s_inputs: Xs_batch,
#                             self.p_inputs: Xp_batch,
#                             self.o_inputs: Xo_batch,
#                             self.y_inputs: y
#                         }
#
#                     _, elbo_value = session.run([self.training_step, self.elbo], feed_dict=loss_args)
#
#                     loss_values += [elbo_value / (Xp_batch.shape[0] / nb_versions)]
#                     total_loss_value += elbo_value
#
#                     counter += 1
#
#                     # for projection_step in projection_steps:
#                     #     session.run([projection_step])
#
#                 def stats(values):
#                     return '{0:.4f} ± {1:.4f}'.format(round(np.mean(values), 4), round(np.std(values), 4))
#
#                 # logger.warn('Epoch: {0}\tELBO: {1}'.format(epoch, stats(loss_values)))
#                 if (round(np.mean(loss_values), 4) < minloss):
#                     minloss = round(np.mean(loss_values), 4)
#                     minepoch = epoch
#                 else:
#
#                     if (round(np.mean(loss_values), 4) < minloss):
#                         minloss = round(np.mean(loss_values), 4)
#                         minepoch = epoch
#
#                     logger.warn('Epoch: {0}\tVLB: {1}'.format(epoch, stats(loss_values)))
#
#                 if (epoch % 200)==0:
#
#                     for eval_type in ['valid']:
#
#                         eval_triples = test_triples
#                         ranks_subj, ranks_obj = [], []
#                         filtered_ranks_subj, filtered_ranks_obj = [], []
#
#                         for _i, (s, p, o) in enumerate(eval_triples):
#                             s_idx, p_idx, o_idx = self.entity_to_idx[s], self.predicate_to_idx[p], self.entity_to_idx[o]
#
#                             Xs_v = np.full(shape=(self.nb_entities,), fill_value=s_idx, dtype=np.int32)
#                             Xp_v = np.full(shape=(self.nb_entities,), fill_value=p_idx, dtype=np.int32)
#                             Xo_v = np.full(shape=(self.nb_entities,), fill_value=o_idx, dtype=np.int32)
#
#                             feed_dict_corrupt_subj = {self.s_inputs: np.arange(self.nb_entities), self.p_inputs: Xp_v,
#                                                       self.o_inputs: Xo_v}
#                             feed_dict_corrupt_obj = {self.s_inputs: Xs_v, self.p_inputs: Xp_v,
#                                                      self.o_inputs: np.arange(self.nb_entities)}
#
#                             # scores of (1, p, o), (2, p, o), .., (N, p, o)
#                             scores_subj = session.run(self.scores, feed_dict=feed_dict_corrupt_subj)
#
#                             # scores of (s, p, 1), (s, p, 2), .., (s, p, N)
#                             scores_obj = session.run(self.scores, feed_dict=feed_dict_corrupt_obj)
#
#                             ranks_subj += [1 + np.sum(scores_subj > scores_subj[s_idx])]
#                             ranks_obj += [1 + np.sum(scores_obj > scores_obj[o_idx])]
#
#                             filtered_scores_subj = scores_subj.copy()
#                             filtered_scores_obj = scores_obj.copy()
#
#                             rm_idx_s = [self.entity_to_idx[fs] for (fs, fp, fo) in all_triples if
#                                         fs != s and fp == p and fo == o]
#                             rm_idx_o = [self.entity_to_idx[fo] for (fs, fp, fo) in all_triples if
#                                         fs == s and fp == p and fo != o]
#
#                             filtered_scores_subj[rm_idx_s] = - np.inf
#                             filtered_scores_obj[rm_idx_o] = - np.inf
#
#                             filtered_ranks_subj += [1 + np.sum(filtered_scores_subj > filtered_scores_subj[s_idx])]
#                             filtered_ranks_obj += [1 + np.sum(filtered_scores_obj > filtered_scores_obj[o_idx])]
#
#                         ranks = ranks_subj + ranks_obj
#                         filtered_ranks = filtered_ranks_subj + filtered_ranks_obj
#
#                         for setting_name, setting_ranks in [('Filtered', filtered_ranks)]:
#                             mean_rank = np.mean(setting_ranks)
#                             k = 10
#                             hits_at_k = np.mean(np.asarray(setting_ranks) <= k) * 100
#                     t1, t2 = mean_rank, hits_at_k
#                     logger.warn('Hits@10 value: {0} %'.format(t2))
#
#             logger.warn("The minimum loss achieved is {0} \t at epoch {1}".format(minloss, minepoch))

# class MoGVKGE:
#     def __init__(self, embedding_size=5,batch_s=14145, lr=0.001, b1=0.9, b2=0.999, eps=1e-08, GPUMode=False, sigma1_e=6.0,sigma1_p=6.0,sigma2_e=1.0,sigma2_p=1.0,mix=6.0,
#                  alt_cost=True,train_mean=True):
#         super().__init__()
#
#         predicate_embedding_size = embedding_size
#         entity_embedding_size = embedding_size
#
#         triples = io.read_triples("data/wn18/wordnet-mlj12-train.txt")  # choose dataset
#         test_triples = io.read_triples("data/wn18/wordnet-mlj12-test.txt")
#
#         self.random_state = np.random.RandomState(0)
#         self.GPUMode = GPUMode
#         self.alt_cost = alt_cost
#         self.nb_examples = len(triples)
#
#         if not (self.GPUMode):
#             logger.warn('Parsing the facts in the Knowledge Base ..')
#
#         # logger.warn('Parsing the facts in the Knowledge Base ..')
#         self.facts = [Fact(predicate_name=p, argument_names=[s, o]) for s, p, o in triples]
#
#         self.test_facts = [Fact(predicate_name=p, argument_names=[s, o]) for s, p, o in test_triples]
#
#         self.test_parser = KnowledgeBaseParser(self.test_facts)
#         self.parser = KnowledgeBaseParser(self.facts)
#
#         ##### for test time ######
#         all_triples = triples + test_triples
#         entity_set = {s for (s, p, o) in all_triples} | {o for (s, p, o) in all_triples}
#         predicate_set = {p for (s, p, o) in all_triples}
#         self.entity_to_idx = {entity: idx for idx, entity in enumerate(sorted(entity_set))}
#         self.predicate_to_idx = {predicate: idx for idx, predicate in enumerate(sorted(predicate_set))}
#         self.nb_entities, self.nb_predicates = len(entity_set), len(predicate_set)
#         ############################
#
#         optimizer = tf.train.AdamOptimizer(learning_rate=lr, beta1=b1, beta2=b2, epsilon=eps)
#         self.build_model(self.nb_entities, entity_embedding_size, self.nb_predicates, predicate_embedding_size,
#                          optimizer,sigma1_e, sigma1_p, sigma2_e, sigma2_p, mix,train_mean)
#
#         self.train(nb_epochs=1000, test_triples=test_triples, all_triples=all_triples,batch_size=batch_s)
#
#     @staticmethod
#     def input_parameters(inputs, parameters_layer):
#         parameters = tf.nn.embedding_lookup(parameters_layer, inputs)
#         mu, log_sigma_square = tf.split(value=parameters, num_or_size_splits=2, axis=1)
#         return mu, log_sigma_square
#
#     @staticmethod
#     def sample_embedding(mu, log_sigma_square):
#         sigma = tf.sqrt(tf.exp(log_sigma_square))
#         embedding_size = mu.get_shape()[1].value
#         eps = tf.random_normal((1, embedding_size), 0, 1, dtype=tf.float32)
#         return mu + sigma * eps
#
#     def build_model(self, nb_entities, entity_embedding_size, nb_predicates, predicate_embedding_size, optimizer,
#                     sigma1_e, sigma1_p, sigma2_e, sigma2_p, mix,train_mean):
#         self.s_inputs = tf.placeholder(tf.int32, shape=[None])
#         self.p_inputs = tf.placeholder(tf.int32, shape=[None])
#         self.o_inputs = tf.placeholder(tf.int32, shape=[None])
#         self.y_inputs = tf.placeholder(tf.bool, shape=[None])
#
#
#         self.build_encoder(nb_entities, entity_embedding_size, nb_predicates, predicate_embedding_size,
#                            sigma1_e, sigma1_p, sigma2_e, sigma2_p, mix,train_mean)
#         self.build_decoder()
#
#         self.KL_discount = tf.placeholder(tf.float32)  # starts at 0.5
#
#         # Kullback Leibler divergence spike
#         self.e_objective = 0.0
#         self.e_objective -= 0.5 * tf.reduce_sum(
#             1. + self.log_sigma_sq_s1 - tf.square(self.mu_s) - tf.exp(self.log_sigma_sq_s1))
#         self.e_objective -= 0.5 * tf.reduce_sum(
#             1. + self.log_sigma_sq_p1 - tf.square(self.mu_p) - tf.exp(self.log_sigma_sq_p1))
#         self.e_objective -= 0.5 * tf.reduce_sum(
#             1. + self.log_sigma_sq_o1 - tf.square(self.mu_o) - tf.exp(self.log_sigma_sq_o1))
#         ## KL Slab
#
#         self.e_objective -= 0.5 * tf.reduce_sum(
#             1. + self.log_sigma_sq_s2 - tf.square(self.mu_s) - tf.exp(self.log_sigma_sq_s2))
#         self.e_objective -= 0.5 * tf.reduce_sum(
#             1. + self.log_sigma_sq_p2 - tf.square(self.mu_p) - tf.exp(self.log_sigma_sq_p2))
#         self.e_objective -= 0.5 * tf.reduce_sum(
#             1. + self.log_sigma_sq_o2 - tf.square(self.mu_o) - tf.exp(self.log_sigma_sq_o2))
#
#         ##compression cost
#         self.e_objective = (self.e_objective * self.KL_discount)
#         # Log likelihood
#         self.g_objective = -tf.reduce_sum(
#             tf.log(tf.where(condition=self.y_inputs, x=self.p_x_i, y=1 - self.p_x_i) + 1e-4))
#
#         self.elbo = self.g_objective + self.e_objective
#
#         self.training_step = optimizer.minimize(self.elbo)
#
#     def build_encoder(self, nb_entities, entity_embedding_size, nb_predicates, predicate_embedding_size,
#                       sigma1_e, sigma1_p, sigma2_e, sigma2_p, mix,train_mean):
#         if not (self.GPUMode):
#             logger.warn('Building Inference Networks q(h_x | x) ..')
#
#         # logger.warn('Building Inference Networks q(h_x | x) ..')
#
#         with tf.variable_scope("encoder"):
#             self.entity_embedding_mean = tf.get_variable('entities_mean',
#                                                          shape=[nb_entities + 1, entity_embedding_size],
#                                                          initializer=tf.zeros_initializer(), dtype=tf.float32,trainable=train_mean)
#             self.entity_embedding_sigm1 = tf.get_variable('entities_sigma1',
#                                                          shape=[nb_entities + 1, entity_embedding_size],
#                                                          initializer=tf.ones_initializer(), dtype=tf.float32)
#
#             self.entity_embedding_sigma1 = tf.Variable(self.entity_embedding_sigm1.initialized_value() * sigma1_e,
#                                                       dtype=tf.float32)
#
#             self.entity_embedding_sigm2 = tf.get_variable('entities_sigma2',
#                                                          shape=[nb_entities + 1, entity_embedding_size],
#                                                          initializer=tf.ones_initializer(), dtype=tf.float32)
#
#             self.entity_embedding_sigma2 = tf.Variable(self.entity_embedding_sigm2.initialized_value() * sigma2_e,
#                                                       dtype=tf.float32)
#
#             self.mu_s = tf.nn.embedding_lookup(self.entity_embedding_mean, self.s_inputs)
#             self.log_sigma_sq_s1 = tf.nn.embedding_lookup(self.entity_embedding_sigma1, self.s_inputs)
#             self.log_sigma_sq_s2 = tf.nn.embedding_lookup(self.entity_embedding_sigma2, self.s_inputs)
#
#             self.h_s1 = VKGE.sample_embedding(self.mu_s, self.log_sigma_sq_s1)
#             self.h_s2 = VKGE.sample_embedding(self.mu_s, self.log_sigma_sq_s2)
#
#             self.h_s = (self.h_s1*mix +(1-mix)*self.h_s2) #MoG
#
#             self.mu_o = tf.nn.embedding_lookup(self.entity_embedding_mean, self.o_inputs)
#             self.log_sigma_sq_o1 = tf.nn.embedding_lookup(self.entity_embedding_sigma1, self.o_inputs)
#             self.log_sigma_sq_o2 = tf.nn.embedding_lookup(self.entity_embedding_sigma2, self.o_inputs)
#
#             self.h_o1 = VKGE.sample_embedding(self.mu_o, self.log_sigma_sq_o1)
#             self.h_o2 = VKGE.sample_embedding(self.mu_o, self.log_sigma_sq_o2)
#
#             self.h_o = (self.h_o1*mix +(1-mix)*self.h_o2) #MoG
#
#             self.predicate_embedding_mean = tf.get_variable('predicate_mean',
#                                                             shape=[nb_predicates + 1, predicate_embedding_size],
#                                                             initializer=tf.zeros_initializer(), dtype=tf.float32,trainable=train_mean)
#             self.predicate_embedding_sigm1 = tf.get_variable('predicate_sigma',
#                                                             shape=[nb_predicates + 1, predicate_embedding_size],
#                                                             initializer=tf.ones_initializer(), dtype=tf.float32)
#
#             self.predicate_embedding_sigma1 = tf.Variable(self.predicate_embedding_sigm1.initialized_value() * pred_sig,
#                                                          dtype=tf.float32)
#             self.predicate_embedding_sigm2 = tf.get_variable('predicate_sigma',
#                                                              shape=[nb_predicates + 1, predicate_embedding_size],
#                                                              initializer=tf.ones_initializer(), dtype=tf.float32)
#
#             self.predicate_embedding_sigma2 = tf.Variable(self.predicate_embedding_sigm1.initialized_value() * pred_sig,dtype=tf.float32)
#
#             self.mu_p = tf.nn.embedding_lookup(self.predicate_embedding_mean, self.p_inputs)
#             self.log_sigma_sq_p1 = tf.nn.embedding_lookup(self.predicate_embedding_sigma1, self.p_inputs)
#             self.log_sigma_sq_p2 = tf.nn.embedding_lookup(self.predicate_embedding_sigma2, self.p_inputs)
#
#             self.h_p1 = VKGE.sample_embedding(self.mu_p, self.log_sigma_sq_p1)
#             self.h_p2 = VKGE.sample_embedding(self.mu_p, self.log_sigma_sq_p2)
#             self.h_p = (self.h_p1*mix +(1-mix)*self.h_p2) #MoG
#
#
#
#     def build_decoder(self):
#         if not (self.GPUMode):
#             logger.warn('Building Inference Network p(y|h) ..')
#         # logger.warn('Building Inference Network p(y|h) ..')
#         with tf.variable_scope('decoder'):
#             model = models.BilinearDiagonalModel(subject_embeddings=self.h_s, predicate_embeddings=self.h_p,
#                                                  object_embeddings=self.h_o)
#             self.scores = model()
#             self.p_x_i = tf.sigmoid(self.scores)
#
#     def train(self, test_triples, all_triples, batch_size, session=0, nb_epochs=1000):
#         index_gen = index.GlorotIndexGenerator()
#         neg_idxs = np.array(sorted(set(self.parser.entity_to_index.values())))
#
#         subj_corruptor = corrupt.SimpleCorruptor(index_generator=index_gen, candidate_indices=neg_idxs,
#                                                  corr_obj=False)
#         obj_corruptor = corrupt.SimpleCorruptor(index_generator=index_gen, candidate_indices=neg_idxs,
#                                                 corr_obj=True)
#
#         train_sequences = self.parser.facts_to_sequences(self.facts)
#
#         Xs = np.array([s_idx for (_, [s_idx, _]) in train_sequences])
#         Xp = np.array([p_idx for (p_idx, _) in train_sequences])
#         Xo = np.array([o_idx for (_, [_, o_idx]) in train_sequences])
#
#         assert Xs.shape == Xp.shape == Xo.shape
#
#         nb_samples = Xs.shape[0]
#         # batch_size = math.ceil(nb_samples / nb_batches)
#         nb_batches= math.ceil(nb_samples / batch_size)
#         # logger.warn("Samples: {}, no. batches: {} -> batch size: {}".format(nb_samples, nb_batches, batch_size))
#         if not (self.GPUMode):
#             logger.warn("Samples: {}, no. batches: {} -> batch size: {}".format(nb_samples, nb_batches, batch_size))
#
#         # projection_steps = [constraints.unit_cube(self.entity_parameters_layer) if unit_cube
#         #                     else constraints.unit_sphere(self.entity_parameters_layer, norm=1.0)]
#         minloss = 10000
#
#         minepoch = 0
#
#         ####### COMPRESSION COST PARAMETERS
#
#         M = int(np.ceil((self.nb_examples * nb_epochs / batch_size)) + 1)
#
#         pi_s = np.log(2.0) * M
#         pi_e = np.log(2.0)
#
#         pi = np.exp(np.linspace(pi_s, pi_e, M) - M * np.log(2.0))
#
#         counter = 0
#
#         #####################
#
#         init_op = tf.global_variables_initializer()
#         with tf.Session() as session:
#             session.run(init_op)
#             for epoch in range(1, nb_epochs + 1):
#                 order = self.random_state.permutation(nb_samples)
#                 Xs_shuf, Xp_shuf, Xo_shuf = Xs[order], Xp[order], Xo[order]
#
#                 Xs_sc, Xp_sc, Xo_sc = subj_corruptor(Xs_shuf, Xp_shuf, Xo_shuf)
#                 Xs_oc, Xp_oc, Xo_oc = obj_corruptor(Xs_shuf, Xp_shuf, Xo_shuf)
#
#                 batches = make_batches(nb_samples, batch_size)
#
#                 loss_values = []
#                 total_loss_value = 0
#
#                 nb_versions = 3
#
#                 for batch_start, batch_end in batches:
#                     curr_batch_size = batch_end - batch_start
#
#                     Xs_batch = np.zeros((curr_batch_size * nb_versions), dtype=Xs_shuf.dtype)
#                     Xp_batch = np.zeros((curr_batch_size * nb_versions), dtype=Xp_shuf.dtype)
#                     Xo_batch = np.zeros((curr_batch_size * nb_versions), dtype=Xo_shuf.dtype)
#
#                     # Positive Example
#                     Xs_batch[0::nb_versions] = Xs_shuf[batch_start:batch_end]
#                     Xp_batch[0::nb_versions] = Xp_shuf[batch_start:batch_end]
#                     Xo_batch[0::nb_versions] = Xo_shuf[batch_start:batch_end]
#
#                     # Negative examples (corrupting subject)
#                     Xs_batch[1::nb_versions] = Xs_sc[batch_start:batch_end]
#                     Xp_batch[1::nb_versions] = Xp_sc[batch_start:batch_end]
#                     Xo_batch[1::nb_versions] = Xo_sc[batch_start:batch_end]
#
#                     # Negative examples (corrupting object)
#                     Xs_batch[2::nb_versions] = Xs_oc[batch_start:batch_end]
#                     Xp_batch[2::nb_versions] = Xp_oc[batch_start:batch_end]
#                     Xo_batch[2::nb_versions] = Xo_oc[batch_start:batch_end]
#
#                     y = np.zeros_like(Xp_batch)
#                     y[0::nb_versions] = 1
#
#                     if self.alt_cost:  # if compression cost
#
#                         loss_args = {
#                             self.KL_discount: pi[counter],
#                             self.s_inputs: Xs_batch,
#                             self.p_inputs: Xp_batch,
#                             self.o_inputs: Xo_batch,
#                             self.y_inputs: y
#                         }
#
#                     else:
#
#                         loss_args = {
#                             self.KL_discount: 1.0,
#                             self.s_inputs: Xs_batch,
#                             self.p_inputs: Xp_batch,
#                             self.o_inputs: Xo_batch,
#                             self.y_inputs: y
#                         }
#
#                     _, elbo_value = session.run([self.training_step, self.elbo], feed_dict=loss_args)
#
#                     loss_values += [elbo_value / (Xp_batch.shape[0] / nb_versions)]
#                     total_loss_value += elbo_value
#
#                     counter += 1
#
#                     # for projection_step in projection_steps:
#                     #     session.run([projection_step])
#
#                 def stats(values):
#                     return '{0:.4f} ± {1:.4f}'.format(round(np.mean(values), 4), round(np.std(values), 4))
#
#                 # logger.warn('Epoch: {0}\tELBO: {1}'.format(epoch, stats(loss_values)))
#                 if self.GPUMode:
#                     if (round(np.mean(loss_values), 4) < minloss):
#                         minloss = round(np.mean(loss_values), 4)
#                         minepoch = epoch
#                 else:
#
#                     if (round(np.mean(loss_values), 4) < minloss):
#                         minloss = round(np.mean(loss_values), 4)
#                         minepoch = epoch
#
#                     logger.warn('Epoch: {0}\tVLB: {1}'.format(epoch, stats(loss_values)))
#
#                 if (epoch % 200)==0:
#
#                     for eval_type in ['valid']:
#
#                         eval_triples = test_triples
#                         ranks_subj, ranks_obj = [], []
#                         filtered_ranks_subj, filtered_ranks_obj = [], []
#
#                         for _i, (s, p, o) in enumerate(eval_triples):
#                             s_idx, p_idx, o_idx = self.entity_to_idx[s], self.predicate_to_idx[p], self.entity_to_idx[o]
#
#                             Xs_v = np.full(shape=(self.nb_entities,), fill_value=s_idx, dtype=np.int32)
#                             Xp_v = np.full(shape=(self.nb_entities,), fill_value=p_idx, dtype=np.int32)
#                             Xo_v = np.full(shape=(self.nb_entities,), fill_value=o_idx, dtype=np.int32)
#
#                             feed_dict_corrupt_subj = {self.s_inputs: np.arange(self.nb_entities), self.p_inputs: Xp_v,
#                                                       self.o_inputs: Xo_v}
#                             feed_dict_corrupt_obj = {self.s_inputs: Xs_v, self.p_inputs: Xp_v,
#                                                      self.o_inputs: np.arange(self.nb_entities)}
#
#                             # scores of (1, p, o), (2, p, o), .., (N, p, o)
#                             scores_subj = session.run(self.scores, feed_dict=feed_dict_corrupt_subj)
#
#                             # scores of (s, p, 1), (s, p, 2), .., (s, p, N)
#                             scores_obj = session.run(self.scores, feed_dict=feed_dict_corrupt_obj)
#
#                             ranks_subj += [1 + np.sum(scores_subj > scores_subj[s_idx])]
#                             ranks_obj += [1 + np.sum(scores_obj > scores_obj[o_idx])]
#
#                             filtered_scores_subj = scores_subj.copy()
#                             filtered_scores_obj = scores_obj.copy()
#
#                             rm_idx_s = [self.entity_to_idx[fs] for (fs, fp, fo) in all_triples if
#                                         fs != s and fp == p and fo == o]
#                             rm_idx_o = [self.entity_to_idx[fo] for (fs, fp, fo) in all_triples if
#                                         fs == s and fp == p and fo != o]
#
#                             filtered_scores_subj[rm_idx_s] = - np.inf
#                             filtered_scores_obj[rm_idx_o] = - np.inf
#
#                             filtered_ranks_subj += [1 + np.sum(filtered_scores_subj > filtered_scores_subj[s_idx])]
#                             filtered_ranks_obj += [1 + np.sum(filtered_scores_obj > filtered_scores_obj[o_idx])]
#
#                         ranks = ranks_subj + ranks_obj
#                         filtered_ranks = filtered_ranks_subj + filtered_ranks_obj
#
#                         for setting_name, setting_ranks in [('Filtered', filtered_ranks)]:
#                             mean_rank = np.mean(setting_ranks)
#                             k = 10
#                             hits_at_k = np.mean(np.asarray(setting_ranks) <= k) * 100
#                     t1, t2 = mean_rank, hits_at_k
#                     logger.warn('Hits@10 value: {0} %'.format(t2))
#
#             logger.warn("The minimum loss achieved is {0} \t at epoch {1}".format(minloss, minepoch))


flags = tf.app.flags
flags.DEFINE_float("learning_rate", 0.001, "Learning rate of adam optimizer [0.001]")
flags.DEFINE_float("beta1", 0.9, "Beta 1 of learning rate [0.9]")
flags.DEFINE_float("beta2", 0.99, "Beta 2 of learning rate [0.99]")
flags.DEFINE_float("init_sig", 6.0, "Initalised variance of variables [6.0]")
flags.DEFINE_float("init_sig2", 6.0, "Initalised variance of variables [6.0]")
flags.DEFINE_float("mog_split", 0.5, "Split between spike and slab [6.0]")
flags.DEFINE_float("epsilon", 1e-08, "Epsilon of learning rate [1e-08]")
flags.DEFINE_integer("embedding_size", 50, "The dimension of graph embeddings [50]")
flags.DEFINE_integer("batch_size", 14145, "Batch Size [14145]")
flags.DEFINE_boolean("alt_cost", True, "Switch for compression cost to be used in training [True]")
flags.DEFINE_boolean("train_mean", False, "Switch as to if mean is fixed at 0 or can train with random normal init [False]")
flags.DEFINE_boolean("alternating_updates", False, "Alternate updates around each distribution[False]")
FLAGS = flags.FLAGS



def main(_):

    logger.warn("creating model")
    
    vkge.VKGE(embedding_size=FLAGS.embedding_size,lr=FLAGS.learning_rate,b1=FLAGS.beta1,b2=FLAGS.beta2,eps=FLAGS.epsilon,ent_sig=FLAGS.init_sig,alt_cost=FLAGS.alt_cost,batch_s=FLAGS.batch_size,
              train_mean=FLAGS.train_mean,alt_updates=FLAGS.alternating_updates)


if __name__ == '__main__':
    tf.app.run()