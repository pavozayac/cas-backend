"""empty message

Revision ID: d1c12703bbff
Revises: 
Create Date: 2021-08-17 17:53:42.833262

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd1c12703bbff'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('reflections')
    op.drop_table('basic_logins')
    op.drop_table('comments')
    op.drop_table('group_requests')
    op.drop_table('tags_reflections')
    op.drop_table('tags')
    op.drop_table('notifications_recipients')
    op.drop_table('foreign_logins')
    op.drop_table('comment_reports')
    op.drop_table('favourites')
    op.drop_table('notifications')
    op.drop_table('avatars')
    op.drop_table('reflection_reports')
    op.drop_table('attachments')
    op.drop_table('profile_avatars')
    op.drop_table('group_avatars')
    op.drop_table('groups')
    op.drop_table('profiles')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('profiles',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('first_name', sa.VARCHAR(length=100), nullable=True),
    sa.Column('last_name', sa.VARCHAR(length=100), nullable=True),
    sa.Column('date_joined', sa.DATE(), nullable=True),
    sa.Column('post_visibility', sa.INTEGER(), nullable=True),
    sa.Column('last_online', sa.DATE(), nullable=True),
    sa.Column('is_moderator', sa.BOOLEAN(), nullable=True),
    sa.Column('is_admin', sa.BOOLEAN(), nullable=True),
    sa.Column('group_id', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('groups',
    sa.Column('id', sa.VARCHAR(length=10), nullable=False),
    sa.Column('name', sa.VARCHAR(), nullable=True),
    sa.Column('graduation_year', sa.INTEGER(), nullable=True),
    sa.Column('date_created', sa.DATE(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('group_avatars',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('saved_path', sa.VARCHAR(), nullable=True),
    sa.Column('filename', sa.VARCHAR(), nullable=True),
    sa.Column('date_added', sa.DATE(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('profile_avatars',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('saved_path', sa.VARCHAR(), nullable=True),
    sa.Column('filename', sa.VARCHAR(), nullable=True),
    sa.Column('date_added', sa.DATE(), nullable=True),
    sa.Column('profile_id', sa.INTEGER(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('attachments',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('reflection_id', sa.INTEGER(), nullable=True),
    sa.Column('saved_path', sa.VARCHAR(), nullable=True),
    sa.Column('filename', sa.VARCHAR(), nullable=True),
    sa.Column('date_uploaded', sa.DATE(), nullable=True),
    sa.ForeignKeyConstraint(['reflection_id'], ['reflections.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('reflection_reports',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('reflection_id', sa.INTEGER(), nullable=True),
    sa.Column('reason', sa.TEXT(), nullable=True),
    sa.Column('date_reported', sa.DATE(), nullable=True),
    sa.ForeignKeyConstraint(['reflection_id'], ['reflections.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('avatars',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('saved_path', sa.VARCHAR(), nullable=True),
    sa.Column('filename', sa.VARCHAR(), nullable=True),
    sa.Column('date_added', sa.DATE(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('notifications',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('content', sa.VARCHAR(length=200), nullable=True),
    sa.Column('date_sent', sa.DATETIME(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('favourites',
    sa.Column('reflection_id', sa.INTEGER(), nullable=True),
    sa.Column('profile_id', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['profile_id'], ['profiles.id'], ),
    sa.ForeignKeyConstraint(['reflection_id'], ['reflections.id'], )
    )
    op.create_table('comment_reports',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('comment_id', sa.INTEGER(), nullable=True),
    sa.Column('reason', sa.TEXT(), nullable=True),
    sa.Column('date_reported', sa.DATE(), nullable=True),
    sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('foreign_logins',
    sa.Column('profile_id', sa.INTEGER(), nullable=False),
    sa.Column('access_token', sa.VARCHAR(), nullable=True),
    sa.Column('expires_at', sa.DATE(), nullable=True),
    sa.Column('method', sa.VARCHAR(), nullable=True),
    sa.ForeignKeyConstraint(['profile_id'], ['profiles.id'], ),
    sa.PrimaryKeyConstraint('profile_id')
    )
    op.create_table('notifications_recipients',
    sa.Column('profile_id', sa.INTEGER(), nullable=True),
    sa.Column('notification_id', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['notification_id'], ['notifications.id'], ),
    sa.ForeignKeyConstraint(['profile_id'], ['profiles.id'], )
    )
    op.create_table('tags',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=50), nullable=True),
    sa.Column('date_added', sa.DATE(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tags_reflections',
    sa.Column('reflection_id', sa.INTEGER(), nullable=True),
    sa.Column('tag_id', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['reflection_id'], ['reflections.id'], ),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], )
    )
    op.create_table('group_requests',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('group_id', sa.VARCHAR(length=10), nullable=True),
    sa.Column('profile_id', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
    sa.ForeignKeyConstraint(['profile_id'], ['profiles.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('comments',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('profile_id', sa.INTEGER(), nullable=True),
    sa.Column('reflection_id', sa.INTEGER(), nullable=True),
    sa.Column('content', sa.VARCHAR(length=200), nullable=True),
    sa.Column('date_added', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['profile_id'], ['profiles.id'], ),
    sa.ForeignKeyConstraint(['reflection_id'], ['reflections.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('basic_logins',
    sa.Column('profile_id', sa.INTEGER(), nullable=False),
    sa.Column('email', sa.VARCHAR(length=100), nullable=True),
    sa.Column('password', sa.VARCHAR(), nullable=True),
    sa.Column('verification_sent', sa.BOOLEAN(), nullable=True),
    sa.Column('verified', sa.BOOLEAN(), nullable=True),
    sa.ForeignKeyConstraint(['profile_id'], ['profiles.id'], ),
    sa.PrimaryKeyConstraint('profile_id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('reflections',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('profile_id', sa.INTEGER(), nullable=True),
    sa.Column('title', sa.VARCHAR(length=100), nullable=True),
    sa.Column('text_content', sa.TEXT(), nullable=True),
    sa.Column('slug', sa.VARCHAR(length=255), nullable=True),
    sa.Column('date_added', sa.DATETIME(), nullable=True),
    sa.Column('creativity', sa.BOOLEAN(), nullable=True),
    sa.Column('activity', sa.BOOLEAN(), nullable=True),
    sa.Column('service', sa.BOOLEAN(), nullable=True),
    sa.ForeignKeyConstraint(['profile_id'], ['profiles.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
