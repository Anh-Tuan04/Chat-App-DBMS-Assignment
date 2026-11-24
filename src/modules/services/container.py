from __future__ import annotations

import atexit
import logging
import os
from dataclasses import dataclass
from typing import Any

from flask import Flask, current_app

from modules.services.auth import AuthService
from modules.services.conversations import ConversationService
from modules.services.messages import MessageService
from modules.services.notifications import NotificationService
from modules.services.relationships import RelationshipService
from modules.services.users import UserService
from shared.ids import SnowflakeIdGenerator
from shared.repositories.mysql.auth_repository import MySQLAuthRepository
from shared.repositories.mysql.notifications_repository import MySQLNotificationRepository
from shared.repositories.mysql.relationships_repository import MySQLRelationshipRepository
from shared.repositories.mysql.users_repository import MySQLUserRepository
from shared.repositories.mysql.users_table import UsersTable

log = logging.getLogger(__name__)


@dataclass(slots=True)
class BackendServices:
    auth: AuthService
    users: UserService
    relationships: RelationshipService
    notifications: NotificationService
    conversations: ConversationService
    messages: MessageService
    cassandra_cluster: Any = None

    def close(self) -> None:
        if self.cassandra_cluster is not None:
            self.cassandra_cluster.shutdown()


def _create_services(session: Any, cluster: Any = None) -> BackendServices:
    from shared.repositories.cassandra.messages_table import CassandraMessageRepository
    from shared.repositories.conversations import MixConversationRepo

    users_table = UsersTable()
    users_repository = MySQLUserRepository(users_table)
    auth_repository = MySQLAuthRepository(users_table)
    relationships_repository = MySQLRelationshipRepository()
    notifications_repository = MySQLNotificationRepository()
    conversations_repository = MixConversationRepo(
        mysql_pool=None,
        cassandra_session=session,
    )
    messages_repository = CassandraMessageRepository(
        session,
        SnowflakeIdGenerator(),
    )

    notifications = NotificationService(
        notifications_repository,
        relationships_repository,
        users_repository,
        conversations_repository,
    )
    conversations = ConversationService(
        conversations_repository,
        users_repository,
        messages_repository,
        relationships_repository,
        notifications,
    )

    return BackendServices(
        auth=AuthService(auth_repository, users_table),
        users=UserService(users_repository, relationships_repository),
        relationships=RelationshipService(
            relationships_repository, users_repository, notifications
        ),
        notifications=notifications,
        conversations=conversations,
        messages=MessageService(
            messages_repository,
            conversations,
            relationships_repository,
        ),
        cassandra_cluster=cluster,
    )


def init_app_services(app: Flask) -> BackendServices:
    """Create and register the application's shared service and repository instances."""
    existing_services = app.extensions.get("backend_services")
    if existing_services is not None:
        return existing_services

    injected_session = app.config.get("CASSANDRA_SESSION")
    cluster = None

    if injected_session is None:
        from cassandra.cluster import Cluster

        contact_points = app.config.get(
            "CASSANDRA_CONTACT_POINTS",
            os.getenv("CASSANDRA_CONTACT_POINTS", "127.0.0.1"),
        )
        if isinstance(contact_points, str):
            contact_points = [host.strip() for host in contact_points.split(",") if host.strip()]
        if not contact_points:
            raise ValueError("CASSANDRA_CONTACT_POINTS must contain at least one host")

        port = int(app.config.get("CASSANDRA_PORT", os.getenv("CASSANDRA_PORT", "9042")))
        if not 1 <= port <= 65535:
            raise ValueError("CASSANDRA_PORT must be between 1 and 65535")
        keyspace = app.config.get(
            "CASSANDRA_KEYSPACE",
            os.getenv("CASSANDRA_KEYSPACE", "chat_app"),
        )

        cluster = Cluster(contact_points=contact_points, port=port)
        try:
            session = cluster.connect(keyspace)
        except Exception:
            log.exception(
                "Could not connect to Cassandra at %s:%s (keyspace=%s)",
                ",".join(contact_points),
                port,
                keyspace,
            )
            cluster.shutdown()
            raise
    else:
        session = injected_session

    try:
        services = _create_services(session, cluster)
    except Exception:
        if cluster is not None:
            cluster.shutdown()
        raise
    app.extensions["backend_services"] = services
    if cluster is not None:
        atexit.register(services.close)
    return services


def get_services() -> BackendServices:
    services = current_app.extensions.get("backend_services")
    if services is None:
        raise RuntimeError("Backend services have not been initialized for this application")
    return services
