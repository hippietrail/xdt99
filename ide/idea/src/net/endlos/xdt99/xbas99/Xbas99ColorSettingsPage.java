package net.endlos.xdt99.xbas99;

import com.intellij.openapi.editor.colors.TextAttributesKey;
import com.intellij.openapi.fileTypes.SyntaxHighlighter;
import com.intellij.openapi.options.colors.AttributesDescriptor;
import com.intellij.openapi.options.colors.ColorDescriptor;
import com.intellij.openapi.options.colors.ColorSettingsPage;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import javax.swing.*;
import java.util.Map;

public class Xbas99ColorSettingsPage implements ColorSettingsPage {
    private static final AttributesDescriptor[] DESCRIPTORS = new AttributesDescriptor[]{
            new AttributesDescriptor("Statement", Xbas99SyntaxHighlighter.STATEMENT),
            new AttributesDescriptor("Function", Xbas99SyntaxHighlighter.FUNCTION),
            new AttributesDescriptor("Variable", Xbas99SyntaxHighlighter.IDENT),
            new AttributesDescriptor("Value", Xbas99SyntaxHighlighter.VALUE),
            new AttributesDescriptor("String", Xbas99SyntaxHighlighter.QSTRING),
            new AttributesDescriptor("Operator", Xbas99SyntaxHighlighter.OPERATOR),
            new AttributesDescriptor("Line Number", Xbas99SyntaxHighlighter.LINO),
            new AttributesDescriptor("Statement Separator", Xbas99SyntaxHighlighter.SEPARATOR),
            new AttributesDescriptor("Comment", Xbas99SyntaxHighlighter.COMMENT),
    };

    @Nullable
    @Override
    public Icon getIcon() {
        return Xbas99Icons.FILE;
    }

    @NotNull
    @Override
    public SyntaxHighlighter getHighlighter() {
        return new Xbas99SyntaxHighlighter();
    }

    @NotNull
    @Override
    public String getDemoText() {
        return "10 REM SAMPLE xdt99 EXTENDED BASIC PROGRAM\n" +
                "20 CALL CLEAR :: CALL SCREEN(9)\n" +
                "30 FOR I=1 TO 9 :: CALL SPRITE(#I,48+I,3+I*0.8,RND*100,RND*200):: NEXT I\n" +
                "40 INPUT \"WHAT IS YOUR NAME?\":NAME$\n" +
                "50 PRINT \"HELLO \";NAME$\n" +
                "60 GO SUB 100 ! PLAY SOUND EFFECT\n" +
                "70 IF NAME$<>\"BYE\" THEN 40\n" +
                "80 END\n" +
                "100 REM SUBROUTINES\n" +
                "110 LET LEN=LEN$(NAME$)+1\n" +
                "120 IF LEN>5 THEN LEN=5\n" +
                "130 FOR J=1 TO LEN :: CALL SOUND(200,110*J,J):: NEXT J\n" +
                "140 RETURN\n" +
                "200 SUB MYSUB(X(,)) :: X(1,1)=0 :: SUBEND\n";
    }

    @Nullable
    @Override
    public Map<String, TextAttributesKey> getAdditionalHighlightingTagToDescriptorMap() {
        return null;
    }

    @NotNull
    @Override
    public AttributesDescriptor[] getAttributeDescriptors() {
        return DESCRIPTORS;
    }

    @NotNull
    @Override
    public ColorDescriptor[] getColorDescriptors() {
        return ColorDescriptor.EMPTY_ARRAY;
    }

    @NotNull
    @Override
    public String getDisplayName() {
        return "xdt99 BASIC";
    }
}
