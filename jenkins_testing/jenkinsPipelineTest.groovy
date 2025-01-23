import com.lesfurets.jenkins.unit.BasePipelineTest
import org.junit.Before
import org.junit.Test

import static org.junit.Assert.*

class JenkinsPipelineTest extends BasePipelineTest {

    @Before
    void setUp() throws Exception {
        super.setUp()

        helper.registerAllowedMethod("sh", [String.class], { cmd ->
            println "Mocked sh step: ${cmd}"
        })

        binding.setVariable('env', [:])
    }

    @Test
    void testMainBranch() {
        // Set environment to simulate building on main branch
        binding.getVariable('env').BRANCH_NAME = 'main'

        def script = loadScript('jenkinsPipeline.groovy')
        script.call()

        assertTrue("Expected greeting for main branch in logs",
                helper.log.contains("Hello from main branch"))
        assertTrue("Expected main branch build simulation",
                helper.log.contains("Building main branch..."))

        assertFalse("Test stage should NOT run without EXECUTE_TESTS=true",
                helper.log.contains("Executing tests..."))
    }

    @Test
    void testFeatureBranchWithTests() {
        binding.getVariable('env').BRANCH_NAME = 'feature/my-feature'
        binding.getVariable('env').EXECUTE_TESTS = 'true'

        def script = loadScript('jenkinsPipeline.groovy')
        script.call()

        assertTrue("Expected greeting from feature branch in logs",
                helper.log.contains("Hello from feature/my-feature"))
        assertTrue("Expected feature branch build simulation",
                helper.log.contains('Building branch feature/my-feature...'))

        assertTrue("Test stage should run with EXECUTE_TESTS=true",
                helper.log.contains("Executing tests..."))
        assertTrue("Expected test simulation in logs",
                helper.log.contains("Running unit tests..."))

        assertTrue("Deploy stage should always run",
                helper.log.contains("Deploy stage"))
    }
}
