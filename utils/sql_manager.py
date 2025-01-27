import psycopg2
import json
import os
import pandas as pd


class SQLManager(object):

    # Use the following code to reset the database:
    # # truncate table_propositions cascade;
    # # ALTER SEQUENCE table_propositions_id_seq RESTART;

    def __init__(self):
        # Get PostgreSQL credentials from environment variables
        self._db_host = os.getenv('DB_HOST')
        self._db_name = os.getenv('DB_NAME')
        self._db_user = os.getenv('DB_USER')
        self._db_password = os.getenv('DB_PASSWORD')
        self._db_port = os.getenv('DB_PORT', '5432')
        self._schema = os.getenv('DB_SCHEMA', 'public')

    def get_db_connection(self):
        # Initialize the PostgreSQL connection
        return psycopg2.connect(
            host=self._db_host,
            dbname=self._db_name,
            user=self._db_user,
            password=self._db_password,
            port=self._db_port,
            options=f'-c search_path={self._schema}'
        )

    # INIT
    def create_tables(self):
        # Create table propositions table if it doesn't exist
        conn = self.get_db_connection()
        c = conn.cursor()

        c.execute(f'''CREATE EXTENSION IF NOT EXISTS citext;''')

        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,  
                        email CITEXT UNIQUE,
                        username CITEXT UNIQUE,
                        name TEXT,
                        surname TEXT,
                        bgg_username TEXT,
                        telegram_username TEXT,
                        is_admin BOOLEAN DEFAULT FALSE,
                        creation_timestamp_tz timestamptz NULL DEFAULT now(),
                        is_banned BOOLEAN DEFAULT FALSE
                    )
                    ''')

        # create a location table to save both system and user locations: system ones are the one without the user id.
        # Table includes fields are street name, city, house number (if any)
        c.execute('''CREATE TABLE IF NOT EXISTS locations (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        street_name TEXT,
                        city TEXT,
                        house_number TEXT,
                        country TEXT,                        
                        alias TEXT NOT NULL,
                        creation_timestamp_tz timestamptz NULL DEFAULT now(),
                        is_default BOOLEAN DEFAULT FALSE
                    )
                    ''')

        # check if in the "location" table exists a row with is_default = True, if not, create a default location
        c.execute('''SELECT count(*) FROM locations WHERE is_default = TRUE''')
        if c.fetchone()[0] == 0:
            """
            DEFAULT_LOCATION_ALIAS="MATCH"
            DEFAULT_LOCATION_COUNTRY="Italia"
            DEFAULT_LOCATION_CITY="Polignano a Mare"
            DEFAULT_LOCATION_STREEN_NAME="Via Don Luigi Sturzo"
            DEFAULT_LOCATION_STREEN_NUMBER="18"
            """
            try:
                default_location_alias = os.environ['DEFAULT_LOCATION_ALIAS']
                default_location_country = os.environ['DEFAULT_LOCATION_COUNTRY']
                default_location_city = os.environ['DEFAULT_LOCATION_CITY']
                default_location_street_name = os.environ['DEFAULT_LOCATION_STREEN_NAME']
                default_location_street_number = os.environ['DEFAULT_LOCATION_STREEN_NUMBER']
                c.execute(f'''
                            INSERT INTO locations (street_name, city, house_number, country, alias, is_default)
                            VALUES (%s, %s, %s, %s, %s, TRUE)
                        ''',
                    (
                        default_location_street_name,
                        default_location_city,
                        default_location_street_number,
                        default_location_country,
                        default_location_alias
                    )
                )
            except KeyError:
                raise AttributeError("Please set the environment variables for the default location: "
                                     "DEFAULT_LOCATION_ALIAS, DEFAULT_LOCATION_COUNTRY, DEFAULT_LOCATION_CITY, "
                                     "DEFAULT_LOCATION_STREEN_NAME, DEFAULT_LOCATION_STREEN_NUMBER")



        c.execute('''CREATE TABLE IF NOT EXISTS table_propositions (
                        id SERIAL PRIMARY KEY,
                        game_name TEXT,
                        max_players INTEGER,
                        date DATE,
                        time TIME,
                        duration INTEGER,
                        notes TEXT,
                        bgg_game_id INTEGER, 
                        proposed_by_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        location_id INTEGER REFERENCES locations(id) ON DELETE SET NULL,
                        expansions JSONB DEFAULT '[]',
                        creation_timestamp_tz timestamptz NULL DEFAULT now()
                    )''')

        c.execute('''CREATE TABLE IF NOT EXISTS joined_players (
                        id SERIAL PRIMARY KEY,
                        table_id INTEGER REFERENCES table_propositions(id) ON DELETE CASCADE,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        creation_timestamp_tz timestamptz NULL DEFAULT now(),
                        UNIQUE(table_id, user_id)
                    )''')

        c.execute('''CREATE OR REPLACE FUNCTION check_max_players()
                     RETURNS trigger
                     LANGUAGE plpgsql
                    AS $function$
                        DECLARE
                            current_player_count INTEGER;
                            max_players_allowed INTEGER;
                        BEGIN
                            -- Get the current count of players joined for this table
                            SELECT COUNT(*)
                            INTO current_player_count
                            FROM joined_players
                            WHERE table_id = NEW.table_id;
                            
                            -- Get the max_players allowed for this table
                            SELECT max_players
                            INTO max_players_allowed
                            FROM table_propositions
                            WHERE id = NEW.table_id;
                            
                            -- Check if adding another player exceeds max_players
                            IF current_player_count + 1 > max_players_allowed THEN
                                RAISE EXCEPTION 'Maximum number of players exceeded for this table';
                            END IF;
                            
                            RETURN NEW;
                        END;
                    $function$
                    ;
                    ''')

        c.execute('''DO $$
                    BEGIN
                        -- Check if the trigger already exists in information_schema.triggers
                        IF NOT EXISTS (
                            SELECT 1
                            FROM information_schema.triggers
                            WHERE trigger_name = 'before_insert_or_update_joined_players'
                        ) THEN
                            -- Create the trigger if it doesn't exist
                            CREATE TRIGGER before_insert_or_update_joined_players
                            BEFORE INSERT OR UPDATE ON joined_players
                            FOR EACH ROW
                            EXECUTE FUNCTION check_max_players();
                        END IF;
                    END $$;
                    ''')

        conn.commit()
        c.close()
        conn.close()

    # LOCATIONS
    def add_user_location(self, user_id, street_name, city, house_number, country, alias):
        conn = self.get_db_connection()
        c = conn.cursor()

        # Insert the new location
        c.execute(f'''
                    INSERT INTO {self._schema}.locations (user_id, street_name, city, house_number, country, alias)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (user_id, street_name, city, house_number, country, alias)
        )
        _id = c.fetchone()[0]

        conn.commit()
        c.close()
        conn.close()

        return _id

    def update_user_locations(self, locations_df):
        conn = self.get_db_connection()
        c = conn.cursor()

        # UPDATE  the locations for the user
        for index, row in locations_df.iterrows():
            c.execute(f'''
                        UPDATE {self._schema}.locations
                        SET street_name = %s,
                            city = %s,
                            house_number = %s,
                            country = %s,
                            alias = %s
                        WHERE id = %s
                    ''', (row['street_name'], row['city'], row['house_number'], row['country'], row['alias'], row['id'])
            )

        conn.commit()
        c.close()
        conn.close()

    def delete_locations(self, location_ids: list):
        conn = self.get_db_connection()
        c = conn.cursor()

        # DELETE the locations for the user
        for location_id in location_ids:
            c.execute(f'''
                        DELETE FROM {self._schema}.locations
                        WHERE id = %s
                    ''', (location_id,)
            )

        conn.commit()
        c.close()
        conn.close()

    def get_user_locations(self, user_id, include_system_ones=False, return_as_df=True):
        conn = self.get_db_connection()
        c = conn.cursor()

        # Get the locations for the user
        if include_system_ones:
            c.execute(f'''
                        SELECT id, street_name, city, house_number, country, alias, user_id, is_default
                        FROM {self._schema}.locations
                        WHERE user_id = %s OR user_id IS NULL
                        ORDER BY id
                    ''', (user_id, )
            )
        else:
            c.execute(f'''
                        SELECT id, street_name, city, house_number, country, alias, user_id, is_default
                        FROM {self._schema}.locations
                        WHERE user_id = %s
                        ORDER BY id
                    ''', (user_id, )
            )

        result = c.fetchall()
        c.close()
        conn.close()

        if return_as_df:
            columns = ['id', 'street_name', 'city', 'house_number', 'country', 'alias', 'user_id', 'is_default']
            result = pd.DataFrame(result, columns=columns)

        return result

    # USERS
    def get_or_create_user(self, email):
        # try to insert into users table a new user with the given email as email, username Null and is_admin false.
        # If, instead, the email is already there, return the user username and is_admin
        username = None
        is_admin = False
        name = None
        surname = None
        bgg_username = None
        telegram_username = None
        is_banned = False

        conn = self.get_db_connection()
        c = conn.cursor()

        # Check if the user exists
        query = f'''
            SELECT 
                id, 
                username, 
                name, 
                surname, 
                bgg_username, 
                telegram_username, 
                is_admin,
                is_banned 
            FROM {self._schema}.users 
            WHERE
                email = %s'''
        # print(query)
        c.execute(query, (email,))

        result = c.fetchone()
        if result:
            _id, username, name, surname, bgg_username, telegram_username, is_admin, is_banned = result
        else:
            # If the user doesn't exist, insert a new user
            c.execute(f'''
                    INSERT INTO {self._schema}.users (email, username, is_admin)
                    VALUES (%s, %s, %s)
                    RETURNING id
                ''', (email, None, False)
            )
            _id = c.fetchone()[0]

        conn.commit()
        c.close()
        conn.close()

        return _id, username, name, surname, bgg_username, telegram_username, is_admin, is_banned

    def set_user(self, email, username, name, surname, bgg_username, telegram_username):
        conn = self.get_db_connection()
        c = conn.cursor()

        # in case the following variables are False/"" will be converted to None
        if not username:
            username = None
        if not name:
            name = None
        if not surname:
            surname = None
        if not bgg_username:
            bgg_username = None
        if not telegram_username:
            telegram_username = None

        try:
            c.execute('''
                    UPDATE users
                    SET username = %s,
                        name = %s,
                        surname = %s,
                        bgg_username = %s,
                        telegram_username = %s
                    WHERE email = %s
                ''', (username, name, surname, bgg_username, telegram_username, email)
            )
        except psycopg2.errors.UniqueViolation:
            raise AttributeError(f"Username {username} already exists. Please choose another one.")
        conn.commit()
        c.close()
        conn.close()

    # TABLES
    def get_table_propositions(self, joined_by_me: bool, filter_username: str, filter_default_location: bool):

        if joined_by_me:
            joined_by_me_clause = "and tp.id in (SELECT table_id FROM joined_players jp WHERE LOWER(joined_user.username) = LOWER(%s))"
        else:
            joined_by_me_clause = "and TRUE"

        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute(
            f'''
                SELECT
                    tp.id,
                    tp.game_name,
                    tp.max_players,
                    tp.date, tp.time,
                    tp.duration,
                    tp.notes,
                    tp.bgg_game_id,
                    tp.proposed_by_user_id,
                    proposing_user.username as proposed_by,
                    count(jp.id) as joined_count,
                    json_agg(joined_user.username) as joined_users,
                    json_agg(jp.user_id) as joined_users_id,
                    loc.alias as location_alias,
                    -- concat loc country, city, street_name, house_number into a single string:
                    concat_ws(' ', loc.country, loc.city, loc.street_name, loc.house_number) as location_full_address,   
                    -- create a new field if loc.user_id is null => True, else False
                    CASE WHEN loc.user_id IS NULL THEN TRUE ELSE FALSE END as is_system_location,
                    expansions                                     
                FROM 
                    table_propositions tp
                    join users proposing_user on proposing_user.id = tp.proposed_by_user_id
                    left join joined_players jp on jp.table_id = tp.id                    
                    left join users joined_user on joined_user.id = jp.user_id
                    left join locations loc on loc.id = tp.location_id
                WHERE
                    TRUE
                    {joined_by_me_clause}
                    -- check if date is in the future with 1 day of margin
                    and tp.date >= current_date - INTERVAL '1 day'
                    and loc.is_default = {filter_default_location}
                group by 
                    tp.id,
                    tp.game_name,
                    tp.max_players,
                    tp.date, tp.time,
                    tp.duration,
                    tp.notes,
                    tp.bgg_game_id,
                    tp.proposed_by_user_id,
                    proposing_user.username,
                    loc.alias,
                    loc.country, loc.city, loc.street_name, loc.house_number,
                    loc.user_id
                order by tp.date, tp.time, tp.id
            ''', (filter_username,)
        )
        propositions = c.fetchall()
        c.close()
        conn.close()

        return propositions

    def create_proposition(self, selected_game, max_players, date_time, time, duration, notes, bgg_game_id, user_id, join_me_by_default, location_id, expansions):
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute('''
                INSERT INTO table_propositions (
                    game_name, 
                    max_players, 
                    date, 
                    time, 
                    duration, 
                    notes, 
                    bgg_game_id, 
                    proposed_by_user_id,
                    location_id,
                    expansions
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            ''', (
                selected_game,
                max_players,
                date_time.strftime('%Y-%m-%d'),
                time.strftime('%H:%M:%S'),
                duration,
                notes,
                bgg_game_id,
                user_id,
                location_id,
                json.dumps(expansions)
            )
        )

        conn.commit()
        last_row_id = c.fetchone()[0]

        if join_me_by_default:
            self.join_table(last_row_id, user_id)

        c.close()
        conn.close()

        return last_row_id

    def leave_table(self, table_id, joined_player_id):
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute(
            '''DELETE FROM joined_players WHERE table_id = %s AND user_id = %s''',
            (table_id, joined_player_id)
        )
        conn.commit()
        c.close()
        conn.close()

    def join_table(self, table_id, user_id):
        conn = self.get_db_connection()
        c = conn.cursor()
        try:
            c.execute(
                '''INSERT INTO joined_players (table_id, user_id) VALUES (%s, %s)''',
                (table_id, user_id)
            )
            conn.commit()
        except psycopg2.IntegrityError as e:
            print(e)
            raise AttributeError("You have already joined this table.")
        finally:
            c.close()
            conn.close()

    def delete_proposition(self, table_id):
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute(
            '''DELETE FROM joined_players WHERE table_id = %s''',
            (table_id,)
        )
        c.execute(
            '''DELETE FROM table_propositions WHERE id = %s''',
            (table_id,)
        )
        conn.commit()
        c.close()
        conn.close()

    def update_table_proposition(self, table_id, game_name, max_players, date, time, duration, notes, bgg_game_id, location_id, expansions):
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute(
            '''
                UPDATE table_propositions
                SET game_name = %s,
                    max_players = %s,
                    date = %s,
                    time = %s,
                    duration = %s,
                    notes = %s,
                    bgg_game_id = %s,
                    location_id = %s,
                    expansions = %s
                WHERE id = %s
            ''',
            (game_name, max_players, date, time, duration, notes, bgg_game_id, location_id, json.dumps(expansions), table_id)
        )
        conn.commit()
        c.close()
        conn.close()