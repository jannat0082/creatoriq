-- ============================================================
-- VibeSignal AI 
-- ============================================================



DROP TABLE IF EXISTS audience_demographics CASCADE;
DROP TABLE IF EXISTS conversions          CASCADE;
DROP TABLE IF EXISTS posts                CASCADE;
DROP TABLE IF EXISTS campaign_creators    CASCADE;
DROP TABLE IF EXISTS campaigns            CASCADE;
DROP TABLE IF EXISTS creators             CASCADE;
DROP TABLE IF EXISTS brands               CASCADE;




CREATE TABLE brands (
    brand_id        SERIAL PRIMARY KEY,
    brand_name      VARCHAR(150) NOT NULL,
    industry        VARCHAR(100),
    target_segment  VARCHAR(100),
    country         VARCHAR(100),
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE creators (
    creator_id                  SERIAL PRIMARY KEY,
    name                        VARCHAR(200) NOT NULL,
    handle                      VARCHAR(100) UNIQUE NOT NULL,
    platform                    VARCHAR(50)
        CHECK (platform IN ('instagram', 'youtube', 'twitter')),
    niche                       VARCHAR(100),
    tier                        VARCHAR(20)
        CHECK (tier IN ('nano', 'micro', 'macro', 'mega')),
    follower_count              INTEGER DEFAULT 0,
    avg_engagement_rate         NUMERIC(5,2),
    estimated_cost_inr          INTEGER,
    country                     VARCHAR(100) DEFAULT 'India',
    primary_language            VARCHAR(50),
    city_tier                   VARCHAR(20)
        CHECK (city_tier IN ('Tier 1', 'Tier 2', 'Tier 3')),
    follower_growth_spike       SMALLINT DEFAULT 0,
    comment_like_ratio          NUMERIC(5,3),
    engagement_variance         NUMERIC(5,2),
    authenticity_risk_score     INTEGER,
    authenticity_risk_level     VARCHAR(10)
        CHECK (authenticity_risk_level IN ('low', 'medium', 'high')),
    audience_authenticity_score INTEGER,
    joined_date                 DATE,
    created_at                  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_creators_platform ON creators(platform);
CREATE INDEX idx_creators_tier     ON creators(tier);
CREATE INDEX idx_creators_niche    ON creators(niche);


CREATE TABLE campaigns (
    campaign_id             SERIAL PRIMARY KEY,
    brand_id                INTEGER NOT NULL
        REFERENCES brands(brand_id) ON DELETE CASCADE,
    campaign_name           VARCHAR(200) NOT NULL,
    objective               VARCHAR(50)
        CHECK (objective IN ('awareness','engagement','traffic','sales')),
    target_segment          VARCHAR(100),
    target_age_group        VARCHAR(20),
    target_niche            VARCHAR(100),
    preferred_platform      VARCHAR(50)
        CHECK (preferred_platform IN ('instagram','youtube','twitter')),
    preferred_creator_tier  VARCHAR(20)
        CHECK (preferred_creator_tier IN ('nano','micro','macro','mixed')),
    total_budget_inr        NUMERIC(14,2) NOT NULL,
    start_date              DATE NOT NULL,
    end_date                DATE NOT NULL,
    status                  VARCHAR(20)
        CHECK (status IN ('draft','active','completed','paused')),
    created_at              TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_dates CHECK (end_date > start_date)
);


CREATE TABLE campaign_creators (
    cc_id                   SERIAL PRIMARY KEY,
    campaign_id             INTEGER NOT NULL
        REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    creator_id              INTEGER NOT NULL
        REFERENCES creators(creator_id) ON DELETE CASCADE,
    creator_fee_inr         NUMERIC(12,2),
    revenue_attributed_inr  NUMERIC(14,2) DEFAULT 0,
    impressions_delivered   BIGINT DEFAULT 0,
    estimated_engagements   INTEGER DEFAULT 0,
    promo_code              VARCHAR(50) UNIQUE,
    status                  VARCHAR(20)
        CHECK (status IN ('invited','confirmed','active','completed')),
    created_at              TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_campaign_creator UNIQUE (campaign_id, creator_id)
);

CREATE TABLE posts (
    post_id               SERIAL PRIMARY KEY,
    creator_id            INTEGER NOT NULL
        REFERENCES creators(creator_id),
    campaign_id           INTEGER
        REFERENCES campaigns(campaign_id),
    platform              VARCHAR(50)
        CHECK (platform IN ('instagram','youtube','twitter')),
    content_format        VARCHAR(50)
        CHECK (content_format IN (
            'reel','short','story','video',
            'image','carousel','text'
        )),
    likes                 INTEGER DEFAULT 0,
    comments              INTEGER DEFAULT 0,
    shares                INTEGER DEFAULT 0,
    saves                 INTEGER DEFAULT 0,
    views                 BIGINT  DEFAULT 0,
    clicks                INTEGER DEFAULT 0,
    reach                 BIGINT  DEFAULT 0,
    post_engagement_rate  NUMERIC(6,2),
    posted_at             TIMESTAMP NOT NULL,
    created_at            TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_posts_creator         ON posts(creator_id);
CREATE INDEX idx_posts_campaign        ON posts(campaign_id);
CREATE INDEX idx_posts_platform_format ON posts(platform, content_format);


CREATE TABLE conversions (
    conversion_id                SERIAL PRIMARY KEY,
    post_id                      INTEGER REFERENCES posts(post_id),
    campaign_id                  INTEGER REFERENCES campaigns(campaign_id),
    creator_id                   INTEGER REFERENCES creators(creator_id),
    creator_performance_profile  VARCHAR(20)
        CHECK (creator_performance_profile IN ('vanity','converter','performer')),
    order_value_inr              NUMERIC(10,2) NOT NULL
        CHECK (order_value_inr > 0),
    promo_code                   VARCHAR(50),
    age_group                    VARCHAR(20)
        CHECK (age_group IN ('18-24','25-34','35-44','45-54','55+')),
    gender                       VARCHAR(20),
    location                     VARCHAR(100),
    device_type                  VARCHAR(30)
        CHECK (device_type IN ('mobile','desktop','tablet')),
    converted_at                 TIMESTAMP NOT NULL
);

CREATE INDEX idx_conv_campaign ON conversions(campaign_id);
CREATE INDEX idx_conv_creator  ON conversions(creator_id);
CREATE INDEX idx_conv_promo    ON conversions(promo_code);


CREATE TABLE audience_demographics (
    demographic_id    SERIAL PRIMARY KEY,
    creator_id        INTEGER NOT NULL
        REFERENCES creators(creator_id) ON DELETE CASCADE,
    demographic_type  VARCHAR(20) NOT NULL
        CHECK (demographic_type IN ('age_group','gender','state')),
    demographic_value VARCHAR(100) NOT NULL,
    percentage_share  NUMERIC(6,2)
        CHECK (percentage_share BETWEEN 0 AND 100),
    recorded_at       DATE NOT NULL
);

CREATE INDEX idx_demo_creator ON audience_demographics(creator_id);
CREATE INDEX idx_demo_type    ON audience_demographics(demographic_type);


SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

SELECT 'brands'               AS tbl, COUNT(*) FROM brands
UNION ALL SELECT 'creators',          COUNT(*) FROM creators
UNION ALL SELECT 'campaigns',         COUNT(*) FROM campaigns
UNION ALL SELECT 'campaign_creators', COUNT(*) FROM campaign_creators
UNION ALL SELECT 'posts',             COUNT(*) FROM posts
UNION ALL SELECT 'conversions',       COUNT(*) FROM conversions
UNION ALL SELECT 'audience_demographics', COUNT(*) FROM audience_demographics
ORDER BY tbl;