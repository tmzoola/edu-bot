--
-- PostgreSQL database dump
--

\restrict iz4tXK75mjIyP5RrwfqaaKKNIKdP2N3ez1QgMhk8uZjGQbquo6MwSeifYZZoWs7

-- Dumped from database version 15.18
-- Dumped by pg_dump version 15.18

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: correct_option_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.correct_option_enum AS ENUM (
    'A',
    'B',
    'C',
    'D'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: books; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.books (
    id integer NOT NULL,
    topic_id integer,
    title character varying(255) NOT NULL,
    author character varying(255),
    description text,
    category character varying(64),
    file_path character varying(512) NOT NULL,
    file_name character varying(255) NOT NULL,
    file_size integer NOT NULL,
    downloads integer NOT NULL,
    "order" integer NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('Asia/Tashkent'::text, now()) NOT NULL,
    updated_at timestamp with time zone DEFAULT timezone('Asia/Tashkent'::text, now()) NOT NULL,
    deleted_at timestamp with time zone
);


--
-- Name: books_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.books_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: books_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.books_id_seq OWNED BY public.books.id;


--
-- Name: modules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.modules (
    title character varying(255) NOT NULL,
    description text,
    icon character varying(64),
    color character varying(32),
    "order" integer NOT NULL,
    is_active boolean NOT NULL,
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('Asia/Tashkent'::text, now()) NOT NULL,
    updated_at timestamp with time zone DEFAULT timezone('Asia/Tashkent'::text, now()) NOT NULL,
    deleted_at timestamp with time zone
);


--
-- Name: modules_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.modules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: modules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.modules_id_seq OWNED BY public.modules.id;


--
-- Name: questions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.questions (
    quiz_id integer NOT NULL,
    text text NOT NULL,
    option_a character varying(512) NOT NULL,
    option_b character varying(512) NOT NULL,
    option_c character varying(512) NOT NULL,
    option_d character varying(512) NOT NULL,
    correct_option public.correct_option_enum NOT NULL,
    explanation text,
    "order" integer NOT NULL,
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('Asia/Tashkent'::text, now()) NOT NULL,
    updated_at timestamp with time zone DEFAULT timezone('Asia/Tashkent'::text, now()) NOT NULL,
    deleted_at timestamp with time zone
);


--
-- Name: questions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.questions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: questions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.questions_id_seq OWNED BY public.questions.id;


--
-- Name: quiz_attempts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.quiz_attempts (
    user_id integer NOT NULL,
    quiz_id integer NOT NULL,
    score integer NOT NULL,
    total integer NOT NULL,
    answers json,
    completed_at timestamp without time zone,
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('Asia/Tashkent'::text, now()) NOT NULL,
    updated_at timestamp with time zone DEFAULT timezone('Asia/Tashkent'::text, now()) NOT NULL,
    deleted_at timestamp with time zone,
    time_taken_seconds integer NOT NULL
);


--
-- Name: quiz_attempts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.quiz_attempts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: quiz_attempts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quiz_attempts_id_seq OWNED BY public.quiz_attempts.id;


--
-- Name: quizzes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.quizzes (
    topic_id integer NOT NULL,
    title character varying(255) NOT NULL,
    description text,
    is_active boolean NOT NULL,
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('Asia/Tashkent'::text, now()) NOT NULL,
    updated_at timestamp with time zone DEFAULT timezone('Asia/Tashkent'::text, now()) NOT NULL,
    deleted_at timestamp with time zone,
    time_limit_seconds integer NOT NULL
);


--
-- Name: quizzes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.quizzes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: quizzes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quizzes_id_seq OWNED BY public.quizzes.id;


--
-- Name: telegram_users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.telegram_users (
    telegram_id bigint NOT NULL,
    username character varying(255),
    first_name character varying(255),
    last_name character varying(255),
    language_code character varying(10),
    is_blocked boolean NOT NULL,
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('Asia/Tashkent'::text, now()) NOT NULL,
    updated_at timestamp with time zone DEFAULT timezone('Asia/Tashkent'::text, now()) NOT NULL,
    deleted_at timestamp with time zone
);


--
-- Name: telegram_users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.telegram_users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: telegram_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.telegram_users_id_seq OWNED BY public.telegram_users.id;


--
-- Name: topics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.topics (
    title character varying(255) NOT NULL,
    description text,
    "order" integer NOT NULL,
    is_active boolean NOT NULL,
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('Asia/Tashkent'::text, now()) NOT NULL,
    updated_at timestamp with time zone DEFAULT timezone('Asia/Tashkent'::text, now()) NOT NULL,
    deleted_at timestamp with time zone,
    module_id integer
);


--
-- Name: topics_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.topics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: topics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.topics_id_seq OWNED BY public.topics.id;


--
-- Name: books id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.books ALTER COLUMN id SET DEFAULT nextval('public.books_id_seq'::regclass);


--
-- Name: modules id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.modules ALTER COLUMN id SET DEFAULT nextval('public.modules_id_seq'::regclass);


--
-- Name: questions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questions ALTER COLUMN id SET DEFAULT nextval('public.questions_id_seq'::regclass);


--
-- Name: quiz_attempts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_attempts ALTER COLUMN id SET DEFAULT nextval('public.quiz_attempts_id_seq'::regclass);


--
-- Name: quizzes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quizzes ALTER COLUMN id SET DEFAULT nextval('public.quizzes_id_seq'::regclass);


--
-- Name: telegram_users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.telegram_users ALTER COLUMN id SET DEFAULT nextval('public.telegram_users_id_seq'::regclass);


--
-- Name: topics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topics ALTER COLUMN id SET DEFAULT nextval('public.topics_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
c4f8a21d9b3e
\.


--
-- Data for Name: books; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.books (id, topic_id, title, author, description, category, file_path, file_name, file_size, downloads, "order", is_active, created_at, updated_at, deleted_at) FROM stdin;
\.


--
-- Data for Name: modules; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.modules (title, description, icon, color, "order", is_active, id, created_at, updated_at, deleted_at) FROM stdin;
Kirish	\N	\N	\N	1	t	1	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
\.


--
-- Data for Name: questions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.questions (quiz_id, text, option_a, option_b, option_c, option_d, correct_option, explanation, "order", id, created_at, updated_at, deleted_at) FROM stdin;
1	… – bu bolaning barkamol shaxs sifatida shakllanishiga qaratilgan bo‘lib, ta’lim va tarbiya jarayonining maqsadlari, vazifalari, tamoyillari, kutilayotgan natijalari, mazmuni va tashkil etilishini belgilaydigan tayanch hujjat hisoblanadi.	rivojlanish xaritasi	namunaviy haftalik reja	davlat o‘quv dasturi	namunaviy yillik mavzuli reja	C	\N	1	1	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
1	O‘zbekiston Respublikasining “Maktabgacha ta’lim va tarbiya to‘g‘risida”gi qonuni qachon qabul qilingan?	2022-yil 4-fevralda	2019-yil 16-dekabrda	2020-yil 22-dekabrda	2018-yil 30-aprelda	B	\N	2	2	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
1	“Ilk qadam” davlat o‘quv dasturi qaysi xalqaro tashkilot bilan birgalikda ishlab chiqilgan?	YUNESKO	AYSESKO	MDH	YUNISEF	D	\N	3	3	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
1	“Ilk qadam” davlat o‘quv dasturi nechta qoʻllanmani oʻz ichiga oladi?	oltita	to‘qqizta	uchta	yettita	A	\N	4	4	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
1	“Ilk qadam” davlat o‘quv dasturi Oʻzbekiston Respublikasining quyidagi qaysi tashkilotlari va muassasalarida qoʻllanilishi majburiy hisoblanadi? 1. “Mehribonlik” uylari maktabgacha ta’lim guruhlarida; 2. Ixtisoslashtirilgan maktablardagi boshlang‘ich sinflarda; 3. Davlat maktabgacha ta’lim tashkilotlarida; 4. Monitoring va uzluksizlikni ta’minlash maqsadida maktabgacha va boshlang‘ich ta’limni nazorat qiluvchi boshqaruv organlarida; 5. Maktabgacha ta’lim sohasida xizmatlar ko‘rsatuvchi nodavlat MTTlarida.	1, 3, 4, 5	2, 3, 4	1, 2, 3, 5	2, 3, 5	A	\N	5	5	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
1	Volontyorlar kimlar?	kuzatuvchilar	vakillar	ijodkorlar	ko‘ngillilar	D	\N	6	6	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
1	Kommunikatsiya bu – …	muloqot	hamkorlik	faoliyat	munosabat	A	\N	7	7	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
1	MTT ta’lim va tarbiya jarayonining tamoyillariga kirmaydigan javob qatorini aniqlang.	o‘yin orqali ta’lim olish va rivojlantirish	MTTning oila, mahalla, maktab bilan hamkorligi	bolaning huquqi, individualligi va rivojlanish imkoniyatlarini hisobga olmaslik	milliy, tarixiy va madaniy an’analar, ma’naviy boyliklarni tan olish va boshqa xalqlar madaniyatiga hurmatda bo‘lish	C	\N	8	8	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
1	“Ilk qadam” davlat o‘quv dasturining II bobi qanday nomlanadi?	Maktabgacha yoshdagi bolalarga ta’lim berishda kompetensiyaviy yondashuv	Rivojlantiruvchi muhitni tashkil qilish	MTT ta’lim va tarbiya jarayonining maqsad va tamoyillari	Bolaning rivojlanish sohalari bo‘yicha yutuqlari	C	\N	9	9	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
1	Qaysi javobda inklyuziv ta’lim atamasiga to‘gri ta’rif berilgan?	ta’lim jarayonida barcha bolalarni bir xil standart asosida o‘qitish, alohida yondashmaslik	ta’lim olishda alohida ehtiyojlari bo‘lgan bolalar uchun ta’lim va tarbiya jarayoni	maxsus guruhlarda faqat malakali bolalarni rivojlantirishga qaratilgan ta’lim	ta’lim jarayonida individual ehtiyojlarni hisobga olmay, qat’iy va standart tartibni qo‘llash	B	\N	10	10	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
2	Qaysi javobda “kompetensiya” atamasiga to‘g‘ri ta’rif berilgan?	bolaning ta’lim jarayonidagi faol ishtirokchilik darajasi	o‘rganilgan bilimlarni kundalik hayotda qo‘llash layoqati	bolaning bilim, ko‘nikma, malaka va qadriyatlari majmui	o‘rganilgan bilimlarni real vaziyatlarda qo‘llay olish darajasi va umumiy tayyorgarligi	C	\N	1	11	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
2	… – bu bolaning belgilangan tartib va odob-ahloq qoidalariga rioya qilgan holda tengdoshlari va kattalar bilan birgalikda ishlash qobiliyati.	ijtimoiy kompetensiya	shaxsiy kompetensiya	kommunikativ kompetensiya	bilish kompetensiyasi	A	\N	2	12	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
2	Shaxsiy kompetensiyaga to‘g‘ri ta’rif berilgan javob variantini belgilang.	bolaning o‘z-o‘ziga g‘amxo‘rlik qilish uchun mas'uliyatni o‘z zimmasiga olish qobiliyatini hamda kundalik hayotini boshqarish va barqaror sog‘lom turmush tarzini amalda qo‘llash mahorati	axborot olish uchun turli xil aloqa vositalari va kanallardan mustaqil foydalanish qobiliyati	bolaning belgilangan tartib va odob-ahloq qoidalariga rioya qilgan holda tengdoshlari va kattalar bilan birgalikda ishlash qobiliyati	atrofdagi odamlar bilan o‘zaro munosabatlarning konstruktiv usullari va vositalariga ega bo‘lishi	A	\N	3	13	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
2	“Jismoniy rivojlanish va sog‘lom turmush tarzining shakllanishi” sohasidagi ta’lim va tarbiya jarayoni yakunida 6-7 yoshli bola: 1. Turli xil faol harakat turlarini uyg‘un holda va maqsadli bajarishni biladi; 2. O‘z harakatlarini hissiyot va sezgi organlari yordamida boshqaradi; 3. Murakkab vaziyatlardan chiqishning amaliy yo‘llarini topadi; 4. Insonning dunyoni o‘zgartirishdagi yaratuvchanlik rolini tushunadi;	2, 3	1, 4	2, 4	1, 2	D	\N	4	14	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
2	“Ijtimoiy-hissiy rivojlanish” sohasidagi ta’lim va tarbiya jarayoni yakunida 6-7 yoshli bola: 1. Olingan bilim va ko‘nikmalardan turli hayotiy vaziyatlarda o‘z ijodiy rejalarini tuzish va tatbiq qilish uchun foydalanadi; 2. Kattalar va tengdoshlar bilan vaziyatga mos ravishda muloqot qiladi; 3. Murakkab vaziyatlardan chiqishning amaliy yo‘llarini topadi; 4. Xavfsiz hayot faoliyati asoslari qoidalariga rioya qiladi; 5. O‘z “Men”i va boshqa insonlarning hayotiy faoliyat muhitidagi roli to‘g‘risida tasavvurga ega bo‘ladi.	2, 3, 5	2, 3, 4	1, 2, 3	1, 4, 5	A	\N	5	15	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
2	O‘quv va hayotiy faoliyat uchun axborotni mustaqil topadi va qo‘llaydi; makon, shakl va vaqtga mos ravishda ish tutadi; predmetlar, voqea-hodisalar va holatlar o‘rtasidagi bog‘liqlikni tushunadi va ularni yaxlit bir butunlik sifatida idrok qiladi. Yuqorida ta’riflarda bolaning qaysi sohadagi kompetensiyalari haqida gap ketmoqda?	nutq, muloqot, o‘qish va yozish malakalar	ijodiy rivojlanish	bilish jarayonining rivojlanishi	ijtimoiy-hissiy rivojlanish	C	\N	6	16	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
2	Bolaning kognitiv va ijtimoiy rivojlanishi hamda dunyoni bilishi uchun zarur vosita?	idrok	hissiyot	fikrlash	nutq	D	\N	7	17	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
2	“Nutq, muloqot, o‘qish va yozish malakalari” sohasidagi kompetensiyalarga kirmaydigan javob qatorini aniqlang.	ona tilida yozishning dastlabki malakalari va vositalaridan foydalanishni biladi	chet tili bo‘yicha dastlabki bilimlarini namoyish etadi	o‘quv va hayotiy faoliyat uchun axborotni mustaqil topadi va qo‘llaydi	badiiy adabiyotga qiziqish bildiradi	C	\N	8	18	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
2	Qaysi sohadagi ta’lim va tarbiya jarayoni yakunida 6-7 yoshli bola turli hayotiy va o‘quv vaziyatlarida mayda motorika ko‘nikmalaridan foydalanish ko‘nikmalariga ega bo‘ladi?	bilish jarayonining rivojlanishi	jismoniy rivojlanish va sog‘lom turmush tarzining shakllanishi	ijodiy rivojlanish	nutq, muloqot, o‘qish va yozish malakalari	B	\N	9	19	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
2	Qaysi kompetensiya bilim olish, o‘qish va o‘rganish; mustaqil ravishda izlanish, tahlil qilish va atrofolamni tushunish uchun kerakli ma'lumotlarni tanlash qobiliyatini o‘z ichiga oladi?	ijtimoiy kompetensiya	bilish kompetensiyasi	kommunikativ kompetensiya	shaxsiy kompetensiya	B	\N	10	20	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
3	1-iyundan 31-avgustgacha MTTlarda tashkil etiladigan davr qanday ataladi?	yozgi pedagogik faoliyat davri	ochiq havoda mashg‘ulotlar mavsumi	yozgi sog‘lomlashtirish davri	bolalarni chiniqtirish davri	C	\N	1	21	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
3	Maktabgacha yoshda yetakchi faoliyat turi qaysi qatorda to‘g‘ri ko‘rsatilgan?	muloqot	ta’lim	o‘yin	musiqa	C	\N	2	22	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
3	Maktabgacha ta’lim tashkilotlarida ta’lim tili va chet tillaridan foydalanish tartibi qaysi hujjat bilan tartibga solinadi?	“Ta’lim to‘g‘risida”gi qonun	“Maktabgacha ta’lim va tarbiya to‘g‘risida”gi qonun	O‘zbekiston Respublikasi Konstitutsiyasi	“Davlat tili to‘g‘risida”gi qonun	D	\N	3	23	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
3	Pedagoglarga bolaning sog‘lig‘i va xavfsizligini ta’minlagan holda, davlat talablariga erishish, rivojlanishning asosiy va barcha sohalaridagi bolaning vakolatlarini ta’minlashga qaratilgan ta’lim faoliyatini amalga oshirishga imkon beradigan tashkillashtirilgan va tuzilgan hujjat bu?	o‘quv rejasi	metodik qo‘llanma	rivojlanish xaritasi	davlat dasturi	A	\N	4	24	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
3	Bolaning rivojlanish xaritasi har bir yosh guruhi uchun alohida yuritiladi va har bir bola uchun bir yilda necha marta to‘ldiriladi?	uch marta	to‘rt marta	ikki marta	besh marta	A	\N	5	25	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
3	Maktabgacha ta’lim tashkilotining yillik mavzuli rejasi kim tomonidan tasdiqlanadi?	maktabgacha ta’lim tashkiloti metodisti	maktabgacha va maktab ta’limi vazirligi	maktabgacha ta’lim tashkiloti pedagogik kengashi	maktabgacha va maktab ta’limi hududiy boshqarmasi	C	\N	6	26	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
3	Ta’lim va tarbiya jarayonini rejalashtirishda maktabgacha ta’lim tashkilotining o‘quv rejasida hududning xususiyatlarini hisobga olgan holda hududiy komponentning necha foizgacha bo‘lishi ko‘zda tutilgan?	50 foizgacha	20 foizgacha	80 foizgacha	40 foizgacha	B	\N	7	27	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
3	… – bu pedagogning ish jurnali bo‘lib, unda ta’lim va tarbiya jarayonining kunlik rejasi aks ettiriladi.	rivojlanish xaritasi	haftalik reja	yillik mavzuli reja	metodik qo‘llanma	B	\N	8	28	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
3	Bu pedagog faoliyatidagi muhim mas’uliyatli ish. Kuzatishlarning maqsadi ta’lim va tarbiya jarayonida bolaning turli bilim va ko‘nikmalardan qanday foydalanishi haqida ma’lumot to‘plashdir. Bolalarni turli joy, vaqt va sharoitlarda kuzatib, pedagog ularning qiziqishlari, kuchli tomonlari va ehtiyojlari haqida to‘liq tasavvurga ega bo‘ladi. Yuqorida qaysi jarayonga ta’rif berilganini aniqlang.	tarbiyalanuvchining shaxsiy yutuqlar portfoliosi	bolani baholash va sinovdan o‘tkazish	tarbiyalanuvchining o‘zlashtirish jadvali	bolaning rivojlanishini kuzatish	D	\N	9	29	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
3	Ta’lim va tarbiya jarayonini rejalashtirishda maktabgacha ta’lim tashkilotining o‘quv rejasida davlat o‘quv dasturida nazarda tutilgan majburiy komponentning miqdori qancha bo‘lishi ko‘zda tutilgan?	60 foiz	80 foiz	20 foiz	40 foiz	B	\N	10	30	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
4	Maktabgacha ta’lim tashkiloti sharoit va imkoniyatlaridan kelib chiqqan holda kamida nechta rivojlanish markazlarini tashkil etishni ta’minlashi kerak?	beshta	uchta	ikkita	to‘rtta	A	\N	1	31	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
4	… – bu tarbiyalanuvchining qiziqishlari va ta’lim talablari asosida tuzilgan, uning barcha qobiliyatlari va iste’dodlarini ochish va rivojlantirish uchun shart- sharoitlarni ta’minlaydigan o‘quv faoliyati dasturi.	shaxsiy mashg‘ulotlar jadvali	maxsus o‘qitish texnologiyasi	individual ta’lim xaritasi	davlat dasturi	C	\N	2	32	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
4	Ingliz tilidan tarjima qilganda „osonlashtirish“, „rag‘batlantirish“, „qulay shart-sharoitlarni yaratish“ ma’nosini anglatuvchi atama qaysi qatorda ko‘rsatilgan?	fasilitatsiya	kvest	kognitiv	motorika	A	\N	3	33	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
4	Rivojlantiruvchi muhit mazmuniga qo‘yiladigan talablarni ularning ta’rifi bilan moslashtiring. 1. xavfsiz a) madaniy va tarixiy qadriyatlarga, milliy va mintaqaviy an’analar, tabiatga, iqlimga bog‘liq xususiyatlar, hududdagi sanoat rivojlanishining o‘ziga xos xususiyatlariga mos bo‘lishi 2. polifunksional b) barcha elementlarni ulardan foydalanishning ishonchliligi va xavfsizligini ta’minlash talablariga muvofiqligini nazarda tutadi 3. mahalliy c) davlat o‘quv dasturining sharoitga mazmuniga mos kelishi, moslashtirilgan materiallar, jihozlar va xona va bino tashqarisidagi inventarlarning xilma-xilligi 4. mazmunan boy d) rivojlantiruvchi muhitning turli tarkibiy qismlaridan xilma-xil foydalanish imkoniyati	1-b, 2-c, 3-a, 4-d	1-b, 2-d, 3-a, 4-c	1-d, 2-c, 3-d, 4-a	1-d, 2-b, 3-a, 4-c	B	\N	4	34	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
4	Fasilitator atamasiga berilgan to‘g‘ri ta’rifni toping.	mashg‘ulotlarni qat’iy reja asosida olib borib, barcha bolalar faoliyatini bir xil usulda boshqaradigan tarbiyachi	bu an’anaviy ta’lim konsepsiyasi doirasida ishlamaydigan, aksincha, bolalarni o‘zlarini o‘rganish uchun yo‘naltiruvchi va yordam beradigan pedagog	qiziqishini oshirish uchun ularga ijobiy ta’sir ko‘rsatadigan, ularning o‘ziga ishonchini orttirish, mustaqil va samarali faoliyatlariga bo‘lgan ehtiyojlarini rag‘batlantirish va qo‘llab-quvvatlashga yordam beradigan qulay muhit yaratish	bu tarbiyalanuvchining qiziqishlari va ta’lim talablari asosida tuzilgan, uning barcha qobiliyatlari va iste’dodlarini ochish va rivojlantirish uchun shart- sharoitlarni ta’minlaydigan o‘quv faoliyati dasturi	B	\N	5	35	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
4	Kvest atamasi ma’nolari to‘liq va to‘g‘ri ko‘rsatilgan javob variantini aniqlang. 1) rag‘batlantirish; 2) sarguzasht; 3) muammo; 4) qulay shart-sharoitlarni yaratish; 5) osonlashtirish; 6) izlanish.	2, 3, 6	1, 4, 5	1, 5, 6	2, 3, 4	A	\N	6	36	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
4	Xulq-atvor ko‘nikmalari odatda nechta komponentdan iborat hisoblanadi?	beshta	uchta	yettita	to‘rtta	D	\N	7	37	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
4	Rivojlantiruvchi muhit mazmuniga qo‘yilgan talablardan biri – oqilonalik. Uning asosiy mazmunini to‘g‘ri aks ettiruvchi javob variantini toping.	madaniy va tarixiy qadriyatlarga, milliy va mintaqaviy an’analar, tabiatga, iqlimga bog‘liq xususiyatlar, hududdagi sanoat rivojlanishining o‘ziga xos xususiyatlariga mos bo‘lishi	guruhda turli joylar, rivojlanish markazlari, shuningdek, bolalarning erkin tanlovini ta’minlaydigan turli xil materiallar, o‘yinlar, o‘yinchoqlar va jihozlarning mavjudligi; o‘yin materialining muntazam ravishda o‘zgartirilishi, bolalarning o‘yin, harakat, bilish va tadqiqot faoliyatini rag‘batlantiradigan yangi buyum va ashyolarning paydo bo‘lishi	davlat o‘quv dasturi va davlat talablariga muvofiq zamonaviy rivojlantiruvchi muhitni yaratish, shuningdek, maktabgacha ta’lim tashkilotining turli ta’lim dasturlarini amalga oshirishni ta’minlash uchun barcha imkoniyatlardan foydalanish; inklyuziv ta’lim tashkil etilgan taqdirda, zarur shart-sharoitlarni ta’minlash	rivojlantiruvchi muhitning turli tarkibiy qismlaridan xilma-xil foydalanish imkoniyati	C	\N	8	38	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
5	Bolalar to‘liq kun davomida bo‘ladigan guruhning namunaviy kun tartibiga muvofiq bolalarni qabul qilish, erkin o‘yin faoliyati, ertalabki badantarbiya jarayoni necha daqiqa davom etishi ko‘zda tutilgan?	40 daqiqa	25 daqiqa	50 daqiqa	30 daqiqa	C	\N	1	39	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
5	… – muhim vosita bo‘lib, uning yordamida pedagoglar davlat talablariga muvofiq muayyan yosh guruhidagi bolalar uchun ta’lim va tarbiya jarayonini tashkil etishning eng maqbul va samarali shakl, metod hamda yo‘llarini belgilaydi.	metodik qo‘llanma	rivojlanish xaritasi	o‘quv rejasi	ta’lim dasturi	D	\N	2	40	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
5	Rivojlanish sohalarini ularga mos ta’lim texnologiyalari bilan moslashtiring. 1. Bilish jarayonning a) o‘yinni almashtirish, rivojlanishi tasviriy hikoyalar tuzish, qayta hikoya qilish, o‘yin mashqlari, ertaklar to‘qish, o‘xshatish (metafora) tuzish, rasm asosida ijodiy hikoyalar tuzish, mnemotexnika va boshqalar 2. Ijtimoiy-hissiy b) loyiha usuli, tadqiqot va rivojlanish ijodiy loyihalar, rolli o‘yinli loyihalar va boshqalar 3. Ijodiy rivojlanish c) musiqiy terapiya, ritmik improvizatsiya, art terapiya, ertak terapiyasi va boshqalar 4. Nutq, muloqot, d) rasm chizishning o‘qish va yozish noan’anaviy usullari, loydan malakalari yasash, applikatsiyalar. Ixtirochilik muammolarini hal qilish nazariyasi (IMHQN) va boshqalar	1-a, 2-d, 3-b, 4-c	1-b, 2-c, 3-d, 4-a	1-b, 2-d, 3-c, 4-a	1-a, 2-c, 3-d, 4-b	B	\N	3	41	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
5	Bolalar to‘liq kun davomida bo‘ladigan guruhning namunaviy kun tartibiga ko‘ra ertalabki davra suhbati davomiyligi qancha bo‘lishi kerak?	30 daqiqa	15 daqiqa	25 daqiqa	10 daqiqa	B	\N	4	42	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
5	Bolalar bilan kun davomida eng esda qolarli va eng qiziqarli bo‘lgan amallarni eslash, amalga oshirilgan ishlarni muhokama qilish va umumlashtirish hamda ertangi kun uchun tadbirlarni rejalashtirish). Yuqoridagi ta’rifda qaysi jarayon haqida so‘z borayotganini toping.	o‘tgan kun refleksiyasi	ertalabki davra suhbati	qo‘shimcha pullik ta’lim	ikkinchi sayr	A	\N	5	43	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
5	Maktabgacha ta’lim tashkilotining ta’lim dasturi kimning buyrug‘i bilan tasdiqlanadi?	MMTV vaziri	tuman MTTB boshlig‘i	MTT direktori	hududiy MTTB boshlig‘i	C	\N	6	44	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
5	Bolalar to‘liq kun davomida bo‘ladigan guruhning namunaviy kun tartibida bolalar uchun ochiq havoda sayrning kunlik davomiyligi kamida qancha bo‘lishi nazarda tutilgan?	3–4 soat	1–2 soat	2–3 soat	30–40 daqiqa	A	\N	7	45	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
5	Ta’lim dasturining qaysi namunaviy tuzilmaviy elementi “umumiy qoidalar”, tushuntirish xati va MTT faoliyatidagi muammolar tahlili kabilarni o‘z ichiga oladi?	mundarija	tashkiliy bo‘lim	maqsadli bo‘lim	titul varag‘i	C	\N	8	46	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
5	Bolalar to‘liq kun davomida bo‘ladigan guruhning namunaviy kun tartibiga muvofiq tushlik jarayonidan keyin qaysi faoliyat turi bilan shug‘ullaniladi?	ta’lim va tarbiya jarayoni	erkin o‘yin faoliyat	tetiklashtiruvchi gimnastika, havo va suv muolajalari	guruh xonasida erkin o‘yin faoliyati	D	\N	9	47	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
5	Iqlim sharoitiga (ochiq havoda, resurslarga ega rivojlanish markazlarida) ko‘ra bolalarning tanlovi bo‘yicha erkin o‘yin faoliyati bu?	o‘tgan kun refleksiyasi	ertalabki davra suhbati	qo‘shimcha pullik ta’lim	ikkinchi sayr	D	\N	10	48	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N
\.


--
-- Data for Name: quiz_attempts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.quiz_attempts (user_id, quiz_id, score, total, answers, completed_at, id, created_at, updated_at, deleted_at, time_taken_seconds) FROM stdin;
1	1	3	10	{"1": "A", "2": "C", "3": "B", "4": "C", "5": "A", "6": "C", "7": "D", "8": "C", "9": "C", "10": "C"}	2026-07-04 09:15:23.915782	1	2026-07-04 14:15:23.914134+00	2026-07-04 14:15:23.914134+00	\N	12
3	1	3	10	{"1": "A", "2": "B", "3": "B", "4": "B", "5": "B", "6": "C", "7": "C", "8": "C", "9": "B", "10": "B"}	2026-07-04 09:17:49.173213	2	2026-07-04 14:17:49.171859+00	2026-07-04 14:17:49.171859+00	\N	15
1	1	2	10	{"1": "B", "2": "C", "3": "C", "4": "D", "5": "A", "6": "C", "7": "D", "8": "D", "9": "C", "10": "C"}	2026-07-04 09:18:28.606109	3	2026-07-04 14:18:28.604879+00	2026-07-04 14:18:28.604879+00	\N	13
5	1	4	10	{"1": "C", "2": "A", "3": "B", "4": "B", "5": "B", "6": "C", "7": "C", "8": "C", "9": "C", "10": "B"}	2026-07-04 10:49:40.183769	4	2026-07-04 15:49:40.182613+00	2026-07-04 15:49:40.182613+00	\N	58
5	2	3	10	{"11": "C", "12": "A", "13": "A", "15": "B"}	2026-07-04 10:55:59.297803	5	2026-07-04 15:55:59.296623+00	2026-07-04 15:55:59.296623+00	\N	300
1	6	2	10	{"1": "B", "17": "B", "25": "C", "28": "B", "31": "C", "35": "A", "36": "A", "42": "C", "43": "B", "47": "C"}	2026-07-04 12:41:50.947157	7	2026-07-04 17:41:50.941856+00	2026-07-04 17:41:50.941856+00	\N	18
5	6	5	10	{"2": "B", "5": "C", "7": "B", "8": "C", "11": "C", "22": "C", "26": "D", "27": "B", "37": "B", "43": "D"}	2026-07-05 07:17:41.718323	8	2026-07-05 12:17:41.713545+00	2026-07-05 12:17:41.713545+00	\N	73
\.


--
-- Data for Name: quizzes; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.quizzes (topic_id, title, description, is_active, id, created_at, updated_at, deleted_at, time_limit_seconds) FROM stdin;
1	Ilk qadam #1	\N	t	1	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N	300
1	Ilk qadam #2	\N	t	2	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N	300
1	Ilk qadam #3	\N	t	3	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N	300
1	Ilk qadam #4	\N	t	4	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N	300
1	Ilk qadam #5	\N	t	5	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N	300
1	🗓 Kunlik test	Har kuni bitta mavzudan 10 ta tasodifiy savol	f	6	2026-07-04 17:38:18.939926+00	2026-07-04 17:38:18.939926+00	\N	600
\.


--
-- Data for Name: telegram_users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.telegram_users (telegram_id, username, first_name, last_name, language_code, is_blocked, id, created_at, updated_at, deleted_at) FROM stdin;
5242562270	maxmudov0013	Махмудов	\N	en	f	3	2026-07-04 14:16:42.301457+00	2026-07-04 14:16:42.301457+00	\N
716437790	mrdarmonov	dmr	\N	uz	f	4	2026-07-04 14:51:45.204065+00	2026-07-04 14:51:45.204065+00	\N
7788121432	muslima_darmon	Muslima	Darmonova	uz	f	5	2026-07-04 15:09:48.189501+00	2026-07-04 15:09:48.189501+00	\N
765001726	murodjon97_official	Murodjon	\N	ru	f	1	2026-07-04 13:25:35.08132+00	2026-07-04 12:41:10.884798+00	\N
8788051587	marmarossa	Unique	\N	ru	f	7	2026-07-06 01:34:18.164527+00	2026-07-06 01:34:18.164527+00	\N
\.


--
-- Data for Name: topics; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.topics (title, description, "order", is_active, id, created_at, updated_at, deleted_at, module_id) FROM stdin;
Ilk qadam	\N	1	t	1	2026-07-04 13:45:27.241301+00	2026-07-04 13:45:27.241301+00	\N	1
\.


--
-- Name: books_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.books_id_seq', 4, true);


--
-- Name: modules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.modules_id_seq', 1, true);


--
-- Name: questions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.questions_id_seq', 48, true);


--
-- Name: quiz_attempts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.quiz_attempts_id_seq', 8, true);


--
-- Name: quizzes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.quizzes_id_seq', 6, true);


--
-- Name: telegram_users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.telegram_users_id_seq', 7, true);


--
-- Name: topics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.topics_id_seq', 1, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: books books_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.books
    ADD CONSTRAINT books_pkey PRIMARY KEY (id);


--
-- Name: modules modules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.modules
    ADD CONSTRAINT modules_pkey PRIMARY KEY (id);


--
-- Name: questions questions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_pkey PRIMARY KEY (id);


--
-- Name: quiz_attempts quiz_attempts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_attempts
    ADD CONSTRAINT quiz_attempts_pkey PRIMARY KEY (id);


--
-- Name: quizzes quizzes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quizzes
    ADD CONSTRAINT quizzes_pkey PRIMARY KEY (id);


--
-- Name: telegram_users telegram_users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.telegram_users
    ADD CONSTRAINT telegram_users_pkey PRIMARY KEY (id);


--
-- Name: topics topics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topics
    ADD CONSTRAINT topics_pkey PRIMARY KEY (id);


--
-- Name: ix_books_deleted_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_books_deleted_at ON public.books USING btree (deleted_at);


--
-- Name: ix_modules_deleted_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_modules_deleted_at ON public.modules USING btree (deleted_at);


--
-- Name: ix_questions_deleted_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_questions_deleted_at ON public.questions USING btree (deleted_at);


--
-- Name: ix_quiz_attempts_deleted_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quiz_attempts_deleted_at ON public.quiz_attempts USING btree (deleted_at);


--
-- Name: ix_quizzes_deleted_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quizzes_deleted_at ON public.quizzes USING btree (deleted_at);


--
-- Name: ix_telegram_users_deleted_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_telegram_users_deleted_at ON public.telegram_users USING btree (deleted_at);


--
-- Name: ix_telegram_users_telegram_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_telegram_users_telegram_id ON public.telegram_users USING btree (telegram_id);


--
-- Name: ix_topics_deleted_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_topics_deleted_at ON public.topics USING btree (deleted_at);


--
-- Name: books books_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.books
    ADD CONSTRAINT books_topic_id_fkey FOREIGN KEY (topic_id) REFERENCES public.topics(id) ON DELETE SET NULL;


--
-- Name: questions questions_quiz_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_quiz_id_fkey FOREIGN KEY (quiz_id) REFERENCES public.quizzes(id) ON DELETE CASCADE;


--
-- Name: quiz_attempts quiz_attempts_quiz_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_attempts
    ADD CONSTRAINT quiz_attempts_quiz_id_fkey FOREIGN KEY (quiz_id) REFERENCES public.quizzes(id) ON DELETE CASCADE;


--
-- Name: quiz_attempts quiz_attempts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_attempts
    ADD CONSTRAINT quiz_attempts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.telegram_users(id) ON DELETE CASCADE;


--
-- Name: quizzes quizzes_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quizzes
    ADD CONSTRAINT quizzes_topic_id_fkey FOREIGN KEY (topic_id) REFERENCES public.topics(id) ON DELETE CASCADE;


--
-- Name: topics topics_module_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topics
    ADD CONSTRAINT topics_module_id_fkey FOREIGN KEY (module_id) REFERENCES public.modules(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

\unrestrict iz4tXK75mjIyP5RrwfqaaKKNIKdP2N3ez1QgMhk8uZjGQbquo6MwSeifYZZoWs7

