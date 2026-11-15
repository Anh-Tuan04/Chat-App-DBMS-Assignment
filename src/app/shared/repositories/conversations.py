# Conversation repositories : Mix from cassandra and MySQL

from __future__ import annotations
 
from app.modules.repositories.conversations import ConversationRepository
from app.shared.repositories.cassandra.user_conversation_table import CasssandraConversationRepo
from app.shared.repositories.mysql.conversations_table import MySQLConversationRepo

class MixConversationRepo(MySQLConversationRepo,
                          CasssandraConversationRepo,
                          ConversationRepository):
    def __init__(self, mysql_pool, cassandra_session):
        MySQLConversationRepo.__init__(self, mysql_pool)
        CasssandraConversationRepo.__init__(self, cassandra_session)
 