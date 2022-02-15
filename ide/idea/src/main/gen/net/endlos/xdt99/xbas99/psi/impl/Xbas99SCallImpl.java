// This is a generated file. Not intended for manual editing.
package net.endlos.xdt99.xbas99.psi.impl;

import java.util.List;
import org.jetbrains.annotations.*;
import com.intellij.lang.ASTNode;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiElementVisitor;
import com.intellij.psi.util.PsiTreeUtil;
import static net.endlos.xdt99.xbas99.psi.Xbas99Types.*;
import com.intellij.extapi.psi.ASTWrapperPsiElement;
import net.endlos.xdt99.xbas99.psi.*;

public class Xbas99SCallImpl extends ASTWrapperPsiElement implements Xbas99SCall {

  public Xbas99SCallImpl(@NotNull ASTNode node) {
    super(node);
  }

  public void accept(@NotNull Xbas99Visitor visitor) {
    visitor.visitSCall(this);
  }

  @Override
  public void accept(@NotNull PsiElementVisitor visitor) {
    if (visitor instanceof Xbas99Visitor) accept((Xbas99Visitor)visitor);
    else super.accept(visitor);
  }

  @Override
  @NotNull
  public List<Xbas99FStr> getFStrList() {
    return PsiTreeUtil.getChildrenOfTypeAsList(this, Xbas99FStr.class);
  }

  @Override
  @NotNull
  public List<Xbas99Nexprn> getNexprnList() {
    return PsiTreeUtil.getChildrenOfTypeAsList(this, Xbas99Nexprn.class);
  }

  @Override
  @NotNull
  public List<Xbas99Sexpr> getSexprList() {
    return PsiTreeUtil.getChildrenOfTypeAsList(this, Xbas99Sexpr.class);
  }

  @Override
  @NotNull
  public Xbas99Subprog getSubprog() {
    return findNotNullChildByClass(Xbas99Subprog.class);
  }

  @Override
  @NotNull
  public List<Xbas99SvarR> getSvarRList() {
    return PsiTreeUtil.getChildrenOfTypeAsList(this, Xbas99SvarR.class);
  }

}