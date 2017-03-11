# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from uCode.celery import app
import tensorflow as tf
from celery.task import Task
from uCode.settings import BASE_DIR

from sneakers import models


class PredictTask(Task):
    # @app.task(trail=True)
    def run(self, pk):
        sneaker = models.Sneaker.objects.get(pk=pk)

        print(sneaker.feature.path)
        image_path = sneaker.feature.path

        # Read in the image_data
        image_data = tf.gfile.FastGFile(image_path, 'rb').read()
        # Loads label file, strips off carriage return

        txt = BASE_DIR + "/tf_files/retrained_labels.txt"
        label_lines = [line.rstrip() for line 
                    in tf.gfile.GFile(txt)]

        # Unpersists graph from file
        pb = BASE_DIR + "/tf_files/retrained_graph.pb"
        with tf.gfile.FastGFile(pb, 'rb') as f:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(f.read())
            _ = tf.import_graph_def(graph_def, name='')

        max_score = 0
        max_human_string = ""
        with tf.Session() as sess:
            # Feed the image_data as input to the graph and get first prediction
            softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')
            predictions = sess.run(softmax_tensor, \
                    {'DecodeJpeg/contents:0': image_data})
            # Sort to show labels of first prediction in order of confidence
            top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
            for node_id in top_k:
                human_string = label_lines[node_id]
                score = predictions[0][node_id]
                print('%s (score = %.5f)' % (human_string, score))
                if(score > max_score):
                    max_score = score
                    max_human_string = human_string

        sneaker.label = max_human_string
        sneaker.save()


app.tasks.register(PredictTask)


@app.task(trail=True)
def dummy_plus(a, b):
    return a + b
