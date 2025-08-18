CREATE TABLE IF NOT EXISTS jenkins_builds (
    id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('aborted', 'success', 'failed')),
    build_number INTEGER NOT NULL,
    duration INTEGER NOT NULL, -- duration in seconds
    url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pipeline_name ON jenkins_builds(pipeline_name);
CREATE INDEX IF NOT EXISTS idx_status ON jenkins_builds(status);
CREATE INDEX IF NOT EXISTS idx_build_number ON jenkins_builds(build_number);
CREATE INDEX IF NOT EXISTS idx_created_at ON jenkins_builds(created_at);

INSERT INTO jenkins_builds (pipeline_name, status, build_number, duration, url) VALUES
('web-app-deployment', 'success', 1, 245, 'http://jenkins.local/job/web-app-deployment/1/'),
('web-app-deployment', 'success', 2, 198, 'http://jenkins.local/job/web-app-deployment/2/'),
('web-app-deployment', 'failed', 3, 67, 'http://jenkins.local/job/web-app-deployment/3/'),
('web-app-deployment', 'success', 4, 312, 'http://jenkins.local/job/web-app-deployment/4/'),
('web-app-deployment', 'success', 5, 289, 'http://jenkins.local/job/web-app-deployment/5/'),
('web-app-deployment', 'aborted', 6, 45, 'http://jenkins.local/job/web-app-deployment/6/'),
('web-app-deployment', 'success', 7, 267, 'http://jenkins.local/job/web-app-deployment/7/'),
('web-app-deployment', 'success', 8, 234, 'http://jenkins.local/job/web-app-deployment/8/'),
('web-app-deployment', 'failed', 9, 89, 'http://jenkins.local/job/web-app-deployment/9/'),
('web-app-deployment', 'success', 10, 298, 'http://jenkins.local/job/web-app-deployment/10/'),

('api-service-build', 'success', 1, 156, 'http://jenkins.local/job/api-service-build/1/'),
('api-service-build', 'success', 2, 143, 'http://jenkins.local/job/api-service-build/2/'),
('api-service-build', 'success', 3, 167, 'http://jenkins.local/job/api-service-build/3/'),
('api-service-build', 'failed', 4, 92, 'http://jenkins.local/job/api-service-build/4/'),
('api-service-build', 'success', 5, 189, 'http://jenkins.local/job/api-service-build/5/'),
('api-service-build', 'success', 6, 176, 'http://jenkins.local/job/api-service-build/6/'),
('api-service-build', 'aborted', 7, 23, 'http://jenkins.local/job/api-service-build/7/'),
('api-service-build', 'success', 8, 201, 'http://jenkins.local/job/api-service-build/8/'),
('api-service-build', 'success', 9, 154, 'http://jenkins.local/job/api-service-build/9/'),
('api-service-build', 'failed', 10, 78, 'http://jenkins.local/job/api-service-build/10/'),

('database-migration', 'success', 1, 89, 'http://jenkins.local/job/database-migration/1/'),
('database-migration', 'success', 2, 95, 'http://jenkins.local/job/database-migration/2/'),
('database-migration', 'success', 3, 102, 'http://jenkins.local/job/database-migration/3/'),
('database-migration', 'success', 4, 87, 'http://jenkins.local/job/database-migration/4/'),
('database-migration', 'failed', 5, 156, 'http://jenkins.local/job/database-migration/5/'),
('database-migration', 'success', 6, 91, 'http://jenkins.local/job/database-migration/6/'),
('database-migration', 'success', 7, 98, 'http://jenkins.local/job/database-migration/7/'),
('database-migration', 'success', 8, 85, 'http://jenkins.local/job/database-migration/8/'),
('database-migration', 'aborted', 9, 34, 'http://jenkins.local/job/database-migration/9/'),
('database-migration', 'success', 10, 93, 'http://jenkins.local/job/database-migration/10/'),

('e2e-test-suite', 'success', 1, 567, 'http://jenkins.local/job/e2e-test-suite/1/'),
('e2e-test-suite', 'failed', 2, 234, 'http://jenkins.local/job/e2e-test-suite/2/'),
('e2e-test-suite', 'success', 3, 612, 'http://jenkins.local/job/e2e-test-suite/3/'),
('e2e-test-suite', 'success', 4, 589, 'http://jenkins.local/job/e2e-test-suite/4/'),
('e2e-test-suite', 'failed', 5, 178, 'http://jenkins.local/job/e2e-test-suite/5/'),
('e2e-test-suite', 'success', 6, 634, 'http://jenkins.local/job/e2e-test-suite/6/'),
('e2e-test-suite', 'aborted', 7, 123, 'http://jenkins.local/job/e2e-test-suite/7/'),
('e2e-test-suite', 'success', 8, 598, 'http://jenkins.local/job/e2e-test-suite/8/'),
('e2e-test-suite', 'success', 9, 645, 'http://jenkins.local/job/e2e-test-suite/9/'),
('e2e-test-suite', 'failed', 10, 289, 'http://jenkins.local/job/e2e-test-suite/10/'),

('security-scan', 'success', 1, 345, 'http://jenkins.local/job/security-scan/1/'),
('security-scan', 'success', 2, 367, 'http://jenkins.local/job/security-scan/2/'),
('security-scan', 'failed', 3, 189, 'http://jenkins.local/job/security-scan/3/'),
('security-scan', 'success', 4, 398, 'http://jenkins.local/job/security-scan/4/'),
('security-scan', 'success', 5, 356, 'http://jenkins.local/job/security-scan/5/'),
('security-scan', 'success', 6, 412, 'http://jenkins.local/job/security-scan/6/'),
('security-scan', 'success', 7, 334, 'http://jenkins.local/job/security-scan/7/'),
('security-scan', 'aborted', 8, 67, 'http://jenkins.local/job/security-scan/8/'),
('security-scan', 'success', 9, 389, 'http://jenkins.local/job/security-scan/9/'),
('security-scan', 'failed', 10, 156, 'http://jenkins.local/job/security-scan/10/');
