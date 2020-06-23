#!/usr/bin/env python

# Copyright 2016 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This application demonstrates how to perform basic operations on topics
with the Cloud Pub/Sub API.
For more information, see the README.md under /pubsub and the documentation
at https://cloud.google.com/pubsub/docs.

Slightly improved logging and typing to match Python3 standard, by Simon Thelin
"""

import argparse
import logging
import time
from os import getenv
from typing import Any, Dict

from google.cloud import pubsub_v1

PROJECT_ID = getenv("PUBSUB_PROJECT_ID", "")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    datefmt="%m-%d %H:%M",
)

LOGGER = logging.getLogger(__name__)


def list_topics(project_id: str = PROJECT_ID) -> None:
    """Lists all Pub/Sub topics in the given project.

    Args:
        project_id (str): pubsub project id

    """
    publisher = pubsub_v1.PublisherClient()
    project_path = publisher.project_path(project_id)

    for topic in publisher.list_topics(project_path):
        LOGGER.info(topic)


def create_topic(topic_id: str, project_id: str = PROJECT_ID) -> None:
    """Create a new Pub/Sub topic.

    Args:
        topic_id (str): given topic_id
        project_id (str): pubsub project id

    """
    topic_id = topic_id

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    topic = publisher.create_topic(topic_path)

    LOGGER.info(f"Topic created: {topic}")


def delete_topic(topic_id: str, project_id: str = PROJECT_ID) -> None:
    """Deletes an existing Pub/Sub topic.

    Args:
        topic_id (str): given topic_id
        project_id (str): pubsub project id

    """
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    publisher.delete_topic(topic_path)

    LOGGER.info(f"Topic deleted: {topic_path}")


def publish_messages(topic_id: str, project_id: str = PROJECT_ID) -> None:
    """Publishes multiple messages to a Pub/Sub topic.

    Args:
        topic_id (str): given topic_id
        project_id (str): pubsub project id

    """

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    for n in range(1, 10):
        data = f"Message number {n}"
        # Data must be a bytestring
        data = data.encode("utf-8")  # type: ignore
        # When you publish a message, the client returns a future.
        future = publisher.publish(topic_path, data=data)
        LOGGER.info(future.result())

    LOGGER.info("Published messages.")


def publish_messages_with_custom_attributes(topic_id: str, project_id: str = PROJECT_ID) -> None:
    """Publishes multiple messages with custom attributes to a Pub/Sub topic.

    Args:
        topic_id (str): given topic_id
        project_id (str): pubsub project id

    """

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    for n in range(1, 10):
        data = f"Message number {n}"

        # Data must be a bytestring
        data = data.encode("utf-8")  # type: ignore

        # Add two attributes, origin and username, to the message
        future = publisher.publish(topic_path, data, origin="python-sample", username="gcp")
        LOGGER.info(future.result())

    LOGGER.info("Published messages with custom attributes.")


def publish_messages_with_error_handler(topic_id: str, project_id: str = PROJECT_ID) -> None:
    """Publishes multiple messages to a Pub/Sub topic with an error handler.

    Args:
        topic_id (str): given topic_id
        project_id (str): pubsub project id

    """

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    futures: Dict[str, Any] = dict()

    def get_callback(f, data):
        def callback(f):
            try:
                LOGGER.info(f.result())
                futures.pop(data)
            except (ValueError, Exception):  # noqa
                LOGGER.error(f"Please handle {f.exception()} for {data}.")

        return callback

    for i in range(10):
        data = str(i)
        futures.update({data: None})

        # When you publish a message, the client returns a future.
        future = publisher.publish(
            topic_path, data=data.encode("utf-8")  # data must be a bytestring.
        )
        futures[data] = future

        # Publish failures shall be handled in the callback function.
        future.add_done_callback(get_callback(future, data))

    # Wait for all the publish futures to resolve before exiting.
    while futures:
        time.sleep(5)

    LOGGER.info("Published message with error handler.")


def publish_messages_with_batch_settings(
    topic_id: str,
    project_id: str = PROJECT_ID,
    max_messages: int = 10,
    max_bytes: int = 1024,
    max_latency=1,
) -> None:
    """Publishes multiple messages to a Pub/Sub topic with batch settings.

    Args:
        topic_id (str): given topic_id
        project_id (str): pubsub project id
        max_messages (int): max messages, default 100
        max_bytes (int): max bytes, default 1 MB
        max_latency (int): max latency, default 10 ms

    """
    # Configure the batch to publish as soon as there is ten messages,
    # one kilobyte of data, or one second has passed.
    batch_settings = pubsub_v1.types.BatchSettings(
        max_messages=max_messages, max_bytes=max_bytes, max_latency=max_latency,
    )
    publisher = pubsub_v1.PublisherClient(batch_settings)
    topic_path = publisher.topic_path(project_id, topic_id)

    # Resolve the publish future in a separate thread.
    def callback(future):
        message_id = future.result()
        LOGGER.info(message_id)

    for n in range(1, 10):
        data = f"Message number {n}"
        # Data must be a bytestring
        data = data.encode("utf-8")  # type: ignore
        future = publisher.publish(topic_path, data=data)
        # Non-blocking. Allow the publisher client to batch multiple messages.
        future.add_done_callback(callback)

    LOGGER.info("Published messages with batch settings.")
    # [END pubsub_publisher_batch_settings]


def publish_messages_with_retry_settings(topic_id: str, project_id: str = PROJECT_ID) -> None:
    """Publishes messages with custom retry settings.

    Args:
        topic_id (str): given topic_id
        project_id (str): pubsub project id

    """

    # Configure the retry settings. Defaults will be overwritten.
    retry_settings = {
        "interfaces": {
            "google.pubsub.v1.Publisher": {
                "retry_codes": {
                    "publish": [
                        "ABORTED",
                        "CANCELLED",
                        "DEADLINE_EXCEEDED",
                        "INTERNAL",
                        "RESOURCE_EXHAUSTED",
                        "UNAVAILABLE",
                        "UNKNOWN",
                    ]
                },
                "retry_params": {
                    "messaging": {
                        "initial_retry_delay_millis": 100,  # default: 100
                        "retry_delay_multiplier": 1.3,  # default: 1.3
                        "max_retry_delay_millis": 60000,  # default: 60000
                        "initial_rpc_timeout_millis": 5000,  # default: 25000
                        "rpc_timeout_multiplier": 1.0,  # default: 1.0
                        "max_rpc_timeout_millis": 600000,  # default: 30000
                        "total_timeout_millis": 600000,  # default: 600000
                    }
                },
                "methods": {
                    "Publish": {"retry_codes_name": "publish", "retry_params_name": "messaging",}
                },
            }
        }
    }

    publisher = pubsub_v1.PublisherClient(client_config=retry_settings)
    topic_path = publisher.topic_path(project_id, topic_id)

    for n in range(1, 10):
        data = f"Message number {n}"

        # Data must be a bytestring
        data = data.encode("utf-8")  # type: ignore
        future = publisher.publish(topic_path, data=data)
        LOGGER.info(future.result())

    LOGGER.info("Published messages with retry settings.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_id", help="Your Google Cloud project ID")

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("list", help=list_topics.__doc__)

    create_parser = subparsers.add_parser("create", help=create_topic.__doc__)
    create_parser.add_argument("topic_id")

    delete_parser = subparsers.add_parser("delete", help=delete_topic.__doc__)
    delete_parser.add_argument("topic_id")

    publish_parser = subparsers.add_parser("publish", help=publish_messages.__doc__)
    publish_parser.add_argument("topic_id")

    publish_with_custom_attributes_parser = subparsers.add_parser(
        "publish-with-custom-attributes", help=publish_messages_with_custom_attributes.__doc__,
    )
    publish_with_custom_attributes_parser.add_argument("topic_id")

    publish_with_error_handler_parser = subparsers.add_parser(
        "publish-with-error-handler", help=publish_messages_with_error_handler.__doc__,
    )
    publish_with_error_handler_parser.add_argument("topic_id")

    publish_with_batch_settings_parser = subparsers.add_parser(
        "publish-with-batch-settings", help=publish_messages_with_batch_settings.__doc__,
    )
    publish_with_batch_settings_parser.add_argument("topic_id")

    publish_with_retry_settings_parser = subparsers.add_parser(
        "publish-with-retry-settings", help=publish_messages_with_retry_settings.__doc__,
    )
    publish_with_retry_settings_parser.add_argument("topic_id")

    args = parser.parse_args()

    if args.command == "list":
        list_topics(project_id=args.project_id)

    elif args.command == "create":
        create_topic(project_id=args.project_id, topic_id=args.topic_id)

    elif args.command == "delete":
        delete_topic(project_id=args.project_id, topic_id=args.topic_id)

    elif args.command == "publish":
        publish_messages(project_id=args.project_id, topic_id=args.topic_id)

    elif args.command == "publish-with-custom-attributes":
        publish_messages_with_custom_attributes(project_id=args.project_id, topic_id=args.topic_id)

    elif args.command == "publish-with-error-handler":
        publish_messages_with_error_handler(project_id=args.project_id, topic_id=args.topic_id)

    elif args.command == "publish-with-batch-settings":
        publish_messages_with_batch_settings(project_id=args.project_id, topic_id=args.topic_id)

    elif args.command == "publish-with-retry-settings":
        publish_messages_with_retry_settings(project_id=args.project_id, topic_id=args.topic_id)
