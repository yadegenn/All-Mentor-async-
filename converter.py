import json
import sqlite3
import os

def convert_databases(source_path, dest_path, source_db_name, dest_db_name):
    with open('data.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    for bot in config['bots']:
        folder_name = bot['Folder_Name']
        source_db = os.path.join(source_path, folder_name, source_db_name)
        dest_db = os.path.join(dest_path, folder_name, dest_db_name)

        if not os.path.exists(os.path.dirname(dest_db)):
            os.makedirs(os.path.dirname(dest_db))

        print(f"Converting {folder_name}...")

        try:
            source_conn = sqlite3.connect(source_db)
            dest_conn = sqlite3.connect(dest_db)
            dest_cursor = dest_conn.cursor()

            # # Convert messages_private to private_messages - REMOVED
            # data = source_conn.execute("SELECT id, message_id, chat_id FROM messages_private").fetchall()
            # dest_cursor.execute(
            #     "CREATE TABLE IF NOT EXISTS private_messages (chat_id INTEGER, message_id INTEGER, local_id INTEGER)")
            # dest_cursor.executemany("INSERT INTO private_messages (chat_id, message_id, local_id) VALUES (?, ?, ?)",
            #                       [(row[2], row[1], row[0]) for row in data])

            # # Convert messages_group to group_messages - REMOVED
            # data = source_conn.execute("SELECT id, message_id, topic_id FROM messages_group").fetchall()
            # dest_cursor.execute(
            #     "CREATE TABLE IF NOT EXISTS group_messages (topic_id INTEGER, message_id INTEGER, local_id INTEGER)")
            # dest_cursor.executemany("INSERT INTO group_messages (topic_id, message_id, local_id) VALUES (?, ?, ?)",
            #                       [(row[2], row[1], row[0]) for row in data])

            # Convert user_topics to users (with deduplication and clearing previous data)
            data = source_conn.execute("SELECT user_id, user_name, topic_id FROM user_topics").fetchall()
            dest_cursor.execute("DELETE FROM users")  # Очистка таблицы перед вставкой
            dest_cursor.execute("CREATE TABLE IF NOT EXISTS users (chat_id INTEGER, topic_id INTEGER, user_name TEXT)")

            unique_users = set()
            users_to_insert = []
            for row in data:
                # Проверяем уникальность комбинации chat_id, topic_id, user_name
                if (row[0], row[2], row[1]) not in unique_users:
                    unique_users.add((row[0], row[2], row[1]))
                    users_to_insert.append((row[0], row[2], row[1]))

            dest_cursor.executemany("INSERT INTO users (chat_id, topic_id, user_name) VALUES (?, ?, ?)",
                                  users_to_insert)

            dest_conn.commit()
            source_conn.close()

            # Delete group_messages and private_messages if they exist in the destination
            dest_cursor.execute("DROP TABLE IF EXISTS group_messages")
            dest_cursor.execute("DROP TABLE IF EXISTS private_messages")
            dest_conn.commit()

            dest_conn.close()

        except Exception as e:
            print(f"Error converting {folder_name}: {str(e)}")

def main():
    source_path = input("Enter source path: ")
    dest_path = input("Enter destination path: ")
    source_db = input("Enter source database name: ")
    dest_db = input("Enter destination database name: ")

    convert_databases(source_path, dest_path, source_db, dest_db)
    print("Conversion completed!")

if __name__ == "__main__":
    main()
