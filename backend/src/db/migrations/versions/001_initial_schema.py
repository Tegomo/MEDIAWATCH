"""Initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-02-06 09:52:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('subscription_plan', sa.Enum('BASIC', 'PRO', 'ENTERPRISE', name='subscriptionplan'), nullable=False),
        sa.Column('subscription_status', sa.Enum('ACTIVE', 'SUSPENDED', 'CANCELED', 'TRIAL', name='subscriptionstatus'), nullable=False),
        sa.Column('keyword_limit', sa.Integer(), nullable=False),
        sa.Column('user_limit', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('ADMIN', 'CLIENT', 'VIEWER', name='userrole'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('supabase_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('supabase_user_id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_supabase_user_id'), 'users', ['supabase_user_id'], unique=True)

    # Create sources table
    op.create_table(
        'sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('url', sa.String(length=512), nullable=False),
        sa.Column('type', sa.Enum('PRESS', 'WHATSAPP', 'RSS', 'API', name='sourcetype'), nullable=False),
        sa.Column('scraper_class', sa.String(length=100), nullable=False),
        sa.Column('scraping_enabled', sa.Boolean(), nullable=False),
        sa.Column('prestige_score', sa.Float(), nullable=False),
        sa.Column('last_scrape_at', sa.DateTime(), nullable=True),
        sa.Column('last_success_at', sa.DateTime(), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create keywords table
    op.create_table(
        'keywords',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('text', sa.String(length=255), nullable=False),
        sa.Column('normalized_text', sa.String(length=255), nullable=False),
        sa.Column('category', sa.Enum('BRAND', 'PRODUCT', 'PERSON', 'COMPETITOR', 'CUSTOM', name='keywordcategory'), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('alert_enabled', sa.Boolean(), nullable=False),
        sa.Column('alert_threshold', sa.Float(), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('total_mentions_count', sa.Integer(), nullable=False),
        sa.Column('last_mention_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_keywords_text'), 'keywords', ['text'], unique=False)
    op.create_index(op.f('ix_keywords_normalized_text'), 'keywords', ['normalized_text'], unique=False)

    # Create articles table
    op.create_table(
        'articles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('url', sa.String(length=1024), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('raw_content', sa.Text(), nullable=False),
        sa.Column('cleaned_content', sa.Text(), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=False),
        sa.Column('scraped_at', sa.DateTime(), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nlp_processed', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url')
    )
    op.create_index(op.f('ix_articles_url'), 'articles', ['url'], unique=True)
    op.create_index(op.f('ix_articles_content_hash'), 'articles', ['content_hash'], unique=False)
    op.create_index(op.f('ix_articles_published_at'), 'articles', ['published_at'], unique=False)
    op.create_index('idx_article_source_hash', 'articles', ['source_id', 'content_hash'], unique=False)

    # Create mentions table
    op.create_table(
        'mentions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('keyword_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('article_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('matched_text', sa.String(length=255), nullable=False),
        sa.Column('match_context', sa.Text(), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=False),
        sa.Column('sentiment_label', sa.Enum('NEGATIVE', 'NEUTRAL', 'POSITIVE', name='sentimentlabel'), nullable=False),
        sa.Column('visibility_score', sa.Float(), nullable=False),
        sa.Column('theme', sa.Enum('POLITICS', 'ECONOMY', 'SPORT', 'SOCIETY', 'TECHNOLOGY', 'CULTURE', 'OTHER', name='theme'), nullable=True),
        sa.Column('extracted_entities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('alert_sent', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.ForeignKeyConstraint(['keyword_id'], ['keywords.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mentions_keyword_id'), 'mentions', ['keyword_id'], unique=False)
    op.create_index(op.f('ix_mentions_article_id'), 'mentions', ['article_id'], unique=False)
    op.create_index(op.f('ix_mentions_detected_at'), 'mentions', ['detected_at'], unique=False)
    op.create_index('idx_mention_keyword_article', 'mentions', ['keyword_id', 'article_id'], unique=True)
    op.create_index('idx_mention_sentiment_date', 'mentions', ['sentiment_label', 'detected_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_mention_sentiment_date', table_name='mentions')
    op.drop_index('idx_mention_keyword_article', table_name='mentions')
    op.drop_index(op.f('ix_mentions_detected_at'), table_name='mentions')
    op.drop_index(op.f('ix_mentions_article_id'), table_name='mentions')
    op.drop_index(op.f('ix_mentions_keyword_id'), table_name='mentions')
    op.drop_table('mentions')
    
    op.drop_index('idx_article_source_hash', table_name='articles')
    op.drop_index(op.f('ix_articles_published_at'), table_name='articles')
    op.drop_index(op.f('ix_articles_content_hash'), table_name='articles')
    op.drop_index(op.f('ix_articles_url'), table_name='articles')
    op.drop_table('articles')
    
    op.drop_index(op.f('ix_keywords_normalized_text'), table_name='keywords')
    op.drop_index(op.f('ix_keywords_text'), table_name='keywords')
    op.drop_table('keywords')
    
    op.drop_table('sources')
    
    op.drop_index(op.f('ix_users_supabase_user_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    op.drop_table('organizations')
    
    # Drop enums
    sa.Enum(name='theme').drop(op.get_bind())
    sa.Enum(name='sentimentlabel').drop(op.get_bind())
    sa.Enum(name='keywordcategory').drop(op.get_bind())
    sa.Enum(name='sourcetype').drop(op.get_bind())
    sa.Enum(name='userrole').drop(op.get_bind())
    sa.Enum(name='subscriptionstatus').drop(op.get_bind())
    sa.Enum(name='subscriptionplan').drop(op.get_bind())
