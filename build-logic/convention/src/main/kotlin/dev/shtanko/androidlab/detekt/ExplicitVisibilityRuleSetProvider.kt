package dev.shtanko.androidlab.detekt

import io.gitlab.arturbosch.detekt.api.Config
import io.gitlab.arturbosch.detekt.api.RuleSet
import io.gitlab.arturbosch.detekt.api.RuleSetProvider

public class ExplicitVisibilityRuleSetProvider : RuleSetProvider {
    public override val ruleSetId: String = RULE_SET_ID

    public override fun instance(config: Config): RuleSet = RuleSet(
        id = ruleSetId,
        rules = listOf(
            ExplicitVisibility(config),
        ),
    )

    private companion object {
        private const val RULE_SET_ID = "architecture"
    }
}
