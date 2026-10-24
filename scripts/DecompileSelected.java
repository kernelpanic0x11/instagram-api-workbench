import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import jadx.api.JadxArgs;
import jadx.api.JadxDecompiler;
import jadx.api.JavaClass;

/** Extract selected classes for static review; never execute the APK. */
public final class DecompileSelected {
    public static void main(String[] arguments) throws Exception {
        if (arguments.length < 3) throw new IllegalArgumentException("Provide APK, output directory, and original class names");
        JadxArgs options = new JadxArgs();
        options.setInputFile(new File(arguments[0]));
        options.setOutDir(new File(arguments[1]));
        options.setSkipResources(true);
        options.setThreadsCount(2);
        options.setRenameValid(false);
        options.setRenamePrintable(false);
        try (JadxDecompiler decompiler = new JadxDecompiler(options)) {
            decompiler.load();
            Path destination = Path.of(arguments[1]);
            Files.createDirectories(destination);
            for (int index = 2; index < arguments.length; index++) {
                JavaClass selected = decompiler.searchJavaClassByOrigFullName(arguments[index]);
                if (selected == null) throw new IllegalArgumentException("Selected class was not found");
                Files.writeString(destination.resolve(arguments[index].replace('.', '_') + ".java"), selected.getCode());
                System.out.println("Extracted " + arguments[index]);
            }
        }
    }
}
