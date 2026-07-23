package dev.shtanko.androidlab.detekt

import io.gitlab.arturbosch.detekt.api.CodeSmell
import io.gitlab.arturbosch.detekt.api.Config
import io.gitlab.arturbosch.detekt.api.Debt
import io.gitlab.arturbosch.detekt.api.Entity
import io.gitlab.arturbosch.detekt.api.Issue
import io.gitlab.arturbosch.detekt.api.Rule
import io.gitlab.arturbosch.detekt.api.Severity
import org.jetbrains.kotlin.lexer.KtTokens
import org.jetbrains.kotlin.psi.KtClassBody
import org.jetbrains.kotlin.psi.KtClassOrObject
import org.jetbrains.kotlin.psi.KtEnumEntry
import org.jetbrains.kotlin.psi.KtFile
import org.jetbrains.kotlin.psi.KtModifierListOwner
import org.jetbrains.kotlin.psi.KtNamedDeclaration
import org.jetbrains.kotlin.psi.KtNamedFunction
import org.jetbrains.kotlin.psi.KtObjectDeclaration
import org.jetbrains.kotlin.psi.KtParameter
import org.jetbrains.kotlin.psi.KtProperty

public class ExplicitVisibility(
    config: Config = Config.empty,
) : Rule(config) {

    public override val issue: Issue = Issue(
        id = javaClass.simpleName,
        severity = Severity.Style,
        description = "Eligible non-local declarations must state their visibility explicitly.",
        debt = Debt.FIVE_MINS,
    )

    public override fun visitClassOrObject(classOrObject: KtClassOrObject) {
        super.visitClassOrObject(classOrObject)
        if (
            classOrObject !is KtEnumEntry &&
            (classOrObject as? KtObjectDeclaration)?.isObjectLiteral() != true &&
            classOrObject.isMemberOrTopLevel()
        ) {
            reportIfVisibilityIsImplicit(classOrObject)
        }
    }

    public override fun visitNamedFunction(function: KtNamedFunction) {
        super.visitNamedFunction(function)
        if (function.isMemberOrTopLevel()) {
            reportIfVisibilityIsImplicit(function)
        }
    }

    public override fun visitProperty(property: KtProperty) {
        super.visitProperty(property)
        if (property.isMemberOrTopLevel()) {
            reportIfVisibilityIsImplicit(property)
        }
    }

    public override fun visitParameter(parameter: KtParameter) {
        super.visitParameter(parameter)
        if (parameter.hasValOrVar() && parameter.isPropertyOfMemberOrTopLevelClass()) {
            reportIfVisibilityIsImplicit(parameter)
        }
    }

    private fun reportIfVisibilityIsImplicit(declaration: KtModifierListOwner) {
        if (declaration.hasExplicitVisibility()) return

        val name = when (declaration) {
            is KtObjectDeclaration -> declaration.name ?: "companion object"
            is KtParameter -> declaration.name ?: "constructor property"
            else -> (declaration as? KtNamedDeclaration)?.name ?: "declaration"
        }
        report(
            CodeSmell(
                issue = issue,
                entity = Entity.from(declaration),
                message = "Declare `$name` with public, internal, private, or protected visibility.",
            ),
        )
    }

    private fun KtModifierListOwner.hasExplicitVisibility(): Boolean =
        hasModifier(KtTokens.PUBLIC_KEYWORD) ||
            hasModifier(KtTokens.INTERNAL_KEYWORD) ||
            hasModifier(KtTokens.PRIVATE_KEYWORD) ||
            hasModifier(KtTokens.PROTECTED_KEYWORD)

    private fun KtModifierListOwner.isMemberOrTopLevel(): Boolean =
        parent is KtFile || parent is KtClassBody

    private fun KtParameter.isPropertyOfMemberOrTopLevelClass(): Boolean =
        generateSequence(parent) { it.parent }
            .filterIsInstance<KtClassOrObject>()
            .firstOrNull()
            ?.isMemberOrTopLevel() == true
}
