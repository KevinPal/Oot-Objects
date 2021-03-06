

import java.awt.Color;
import java.awt.image.BufferedImage;
import java.awt.print.PrinterGraphics;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.RandomAccessFile;

import javax.imageio.ImageIO;
import javax.swing.ImageIcon;
import javax.swing.JFrame;
import javax.swing.JLabel;

public class TextureConvert {

	public static void main(String[] args) throws IOException {
		String rompath = "D:\\Programming\\Zelda\\zootr\\Decompress\\decomp.z64";
		String texturepath = "D:\\Programming\\Zelda\\Object Dump\\text3.png";

		File rom = new File(rompath);
		File texture = new File(texturepath);

		int width = 32;
		int height = 64;

		int gamePlayKeepStart = 0x00F03000;
		int textOffset = 0x400;

		viewTexture(gamePlayKeepStart + textOffset, width, height, rom); // View a texture from the rom
		int[][] alphas = getAlphas(gamePlayKeepStart + textOffset, width, height, rom); // Get the alpha values from a
																							// texture in rom
		byte[] data = convertTexture(width, height, alphas, texture); // Convert an image (gets printed out for now), using the alpha
														// values from above
		
		writeTexture(data, gamePlayKeepStart + textOffset, rom);

	}
	
	public static void writeTexture(byte[] data, int address, File rom) throws IOException {
		RandomAccessFile fh = new RandomAccessFile(rom, "rw");
		fh.seek(address);
		fh.write(data, 0, data.length);
		fh.close();
	}

	public static byte[] convertTexture(int width, int height, int[][] alphas, File f) throws IOException {

		BufferedImage out = ImageIO.read(f);
		byte[] data = new byte[width * height * 2];
		System.out.println(data.length);
		for (int y = 0; y < height; y++) {
			for (int x = 0; x < width; x++) {
				int rgb = out.getRGB(x, y);
				Color c = new Color(rgb);
				int r = c.getRed();
				int g = c.getGreen();
				int b = c.getBlue();
				int output = 0;

				r = (int) (Math.ceil(r * 31 / 255d));
				g = (int) (Math.ceil(g * 31 / 255d));
				b = (int) (Math.ceil(b * 31 / 255d));
				output |= ((r & 0x1F) << 11);
				output |= ((g & 0x1F) << 6);
				output |= ((b & 0x1F) << 1);
				output |= alphas[y][x];
				data[2 * (y * width + x)] = (byte) ((output & 0xFF00) >> 8);
				data[2 * (y * width + x) + 1] = (byte) ((output & 0x00FF));
				String outstring = Integer.toHexString(output);
				while (outstring.length() < 4) {
					outstring = "0" + outstring;
				}
				System.out.println(outstring);
			}

		}
		return data;
	}

	public static void viewTexture(int offset, int width, int height, File f) throws IOException {

		BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);
		InputStream inputStream = new FileInputStream(f);
		// Very ineffecient, but im lazy
		int counter = 0;
		byte[] temp = new byte[0x10];
		while (counter < (offset) / 0x10) {
			counter++;
			int read = inputStream.read(temp);
		}

		for (int y = 0; y < height; y++) {
			for (int x = 0; x < width; x++) {
				int byte1 = inputStream.read();
				int byte2 = inputStream.read();
				int r = byte1 >> 3;
				int g = ((byte1 & 0x7) << 2) | ((byte2 & 0xC0) >> 6);
				int b = (byte2 & 0x3E) >> 1;
				r = (int) (Math.floor(r * 255 / 31d));
				g = (int) (Math.floor(g * 255 / 31d));
				b = (int) (Math.floor(b * 255 / 31d));
				r = r < 0 ? r + 255 : r;
				g = g < 0 ? g + 255 : g;
				b = b < 0 ? b + 255 : b;
				image.setRGB(x, y, new Color(r, g, b).getRGB());
			}
		}

		inputStream.close();
		
		JFrame frame = new JFrame();
		frame.add(new JLabel(new ImageIcon(image)));
		frame.pack();
		frame.setLocationRelativeTo(null);
		frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		frame.setVisible(true);

	}

	public static int[][] getAlphas(int offset, int width, int height, File f) throws IOException {

		BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);
		InputStream inputStream = new FileInputStream(f);
		// Very ineffecient, but im lazy
		int counter = 0;
		byte[] temp = new byte[0x10];
		while (counter < (offset) / 0x10) {
			counter++;
			int read = inputStream.read(temp);
		}

		int[][] alphas = new int[height][width];

		for (int y = 0; y < height; y++) {
			for (int x = 0; x < width; x++) {
				int byte1 = inputStream.read();
				int byte2 = inputStream.read();
				alphas[y][x] = byte2 & 0x1;
			}
		}
		inputStream.close();
		return alphas;

	}

}
